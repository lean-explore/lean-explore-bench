"""Compare model-card-compatible reranking on every labelled request's fixed pool."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from collection import digest, write


async def run(args):
    os.environ.update(
        OMP_NUM_THREADS="2",
        MKL_NUM_THREADS="2",
        TOKENIZERS_PARALLELISM="false",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    import torch
    from lean_explore.search.engine import SearchEngine
    from lean_explore.search.ranking import combine_rerank_scores, rerank_document
    from lean_explore.util.reranker_client import RerankerClient

    cases = json.loads(args.cases.read_text())["cases"]
    selected = [c for c in cases if any(m["targets"] for m in c["memberships"])]
    expected = {c["id"] for c in selected}
    records = {}
    with (args.base / "records.jsonl").open() as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                break
            if record["query_id"] in expected:
                records[record["query_id"]] = record
            if set(records) == expected:
                break
    if set(records) != expected:
        raise ValueError("All labelled baseline pools must be complete")
    base = json.loads((args.base / "contract.json").read_text())
    if digest(args.cases) != base["cases_sha256"]:
        raise ValueError("Cases changed")
    if (
        digest(args.data / "lean_explore.db")
        != base["data_files_sha256"]["lean_explore.db"]
    ):
        raise ValueError("Corpus changed")
    args.out.mkdir(parents=True, exist_ok=False)
    write(
        args.out / "contract.json",
        dict(
            base_contract_sha256=digest(args.base / "contract.json"),
            cases_sha256=digest(args.cases),
            scheduled_ids=[c["id"] for c in selected],
            selection="Every request with at least one recorded target; no subsampling.",
            conditions=["chat_yes_no_256", "chat_yes_no_512"],
            runner_sha256=digest(__file__),
            rationale="Adapter contract audit; exploratory comparison, no model tuning.",
            instruction="Find relevant Lean 4 math declarations",
            system_instruction="Does the document satisfy the query and instruction? Answer yes or no.",
            reference="https://huggingface.co/Qwen/Qwen3-Reranker-0.6B",
        ),
    )
    (args.out / "executed_runner.py").write_bytes(Path(__file__).read_bytes())
    write(
        args.out / "baseline-pools.json",
        {
            k: dict(
                status=v["status"],
                candidate_ids=(v.get("fixed_pool") or {}).get("candidate_ids", []),
                visible_ids=[r["id"] for r in v["results"]],
            )
            for k, v in records.items()
        },
    )

    class ChatReranker(RerankerClient):
        @torch.no_grad()
        def _compute_scores_sync(self, pairs):
            prefix = "<|im_start|>system\nDoes the document satisfy the query and instruction? Answer yes or no.<|im_end|>\n<|im_start|>user\n"
            suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
            before = self.tokenizer.encode(prefix, add_special_tokens=False)
            after = self.tokenizer.encode(suffix, add_special_tokens=False)
            encoded = self.tokenizer(
                pairs,
                padding=False,
                truncation=True,
                max_length=self.max_length - len(before) - len(after),
                add_special_tokens=False,
                return_attention_mask=False,
            )
            encoded["input_ids"] = [
                before + ids + after for ids in encoded["input_ids"]
            ]
            inputs = self.tokenizer.pad(encoded, padding=True, return_tensors="pt").to(
                self.device
            )
            logits = self.model(**inputs).logits[:, -1, :]
            yes = self.tokenizer.convert_tokens_to_ids("yes")
            no = self.tokenizer.convert_tokens_to_ids("no")
            scores = torch.softmax(
                torch.stack([logits[:, no], logits[:, yes]], dim=1), dim=1
            )[:, 1]
            return scores.cpu().tolist()

    models = base["models"]
    client = ChatReranker(
        model_name=models["Qwen/Qwen3-Reranker-0.6B"]["path"],
        max_length=256,
        batch_size=16,
    )
    engine = SearchEngine(
        db_url=f"sqlite+aiosqlite:///{args.data}/lean_explore.db",
        data_directory=args.data,
        reranker_client=client,
    )
    try:
        with (args.out / "records.jsonl").open("w") as stream:
            for i, case in enumerate(selected):
                baseline = records[case["id"]]
                ids = (baseline.get("fixed_pool") or {}).get("candidate_ids", [])
                visible = {r["id"] for r in baseline["results"]}
                record = dict(
                    query_id=case["id"],
                    baseline_status=baseline["status"],
                    candidate_ids=ids,
                    conditions={},
                )
                if baseline["status"] == "ok":
                    loaded = await engine._load_declarations(ids)
                    if set(loaded) != set(ids):
                        raise ValueError("Pinned candidate missing from corpus")
                    candidates = [loaded[cid] for cid in ids]
                    documents = [rerank_document(d) for d in candidates]
                    for length in (256, 512):
                        client.max_length = length
                        response = await client.rerank(case["query"], documents)
                        mixed = (
                            combine_rerank_scores(
                                case["query"], candidates, response.scores
                            )
                            if candidates
                            else []
                        )
                        record["conditions"][f"chat_yes_no_{length}"] = dict(
                            scores=response.scores,
                            mixed_scores=mixed,
                            neural=[
                                cid
                                for cid, s in sorted(
                                    zip(ids, response.scores),
                                    key=lambda p: p[1],
                                    reverse=True,
                                )
                                if cid in visible
                            ],
                            mixture=[
                                cid
                                for cid, s in sorted(
                                    zip(ids, mixed), key=lambda p: p[1], reverse=True
                                )
                                if cid in visible
                            ],
                        )
                stream.write(json.dumps(record, separators=(",", ":")) + "\n")
                stream.flush()
                if (i + 1) % 25 == 0:
                    os.fsync(stream.fileno())
                    write(
                        args.out / "progress.json",
                        dict(completed=i + 1, scheduled=len(selected)),
                    )
                    print(
                        json.dumps(dict(completed=i + 1, scheduled=len(selected))),
                        flush=True,
                    )
        write(
            args.out / "complete.json",
            dict(
                completed=len(selected),
                records_sha256=digest(args.out / "records.jsonl"),
            ),
        )
    finally:
        await engine.engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "base", "data", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
