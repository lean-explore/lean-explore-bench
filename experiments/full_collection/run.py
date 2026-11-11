"""Replay the full collection locally, with a durable journal and strict resume."""

import argparse
import asyncio
import dataclasses
import json
import os
import random
import sqlite3
import time
from pathlib import Path

from collection import digest, write


def completed_ids(journal, scheduled):
    """Refuse changed ordering, duplicate IDs, corrupt lines and missing prefixes."""
    completed = []
    if journal.exists():
        with journal.open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                i = len(completed)
                if i >= len(scheduled) or record["query_id"] != scheduled[i]:
                    raise ValueError("Journal is not a prefix of the frozen schedule")
                if record["status"] not in {"ok", "error"}:
                    raise ValueError("Journal contains an unfinished record")
                completed.append(record["query_id"])
    return completed


async def run(args):
    os.environ.update(
        OMP_NUM_THREADS="4",
        MKL_NUM_THREADS="4",
        TOKENIZERS_PARALLELISM="false",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        LEAN_EXPLORE_EMBEDDING_BATCH_SIZE="32",
        LEAN_EXPLORE_RERANKER_BATCH_SIZE="16",
    )
    import numpy as np
    import torch
    import lean_explore
    from lean_explore.search.engine import SearchEngine, _top_results
    from lean_explore.search.ranking import (
        RerankWeights,
        combine_rerank_scores,
        rerank_document,
    )
    from lean_explore.search.trace import SearchTrace, record_stage

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    scheduled = [c["id"] for c in cases]
    if len(set(scheduled)) != len(scheduled):
        raise ValueError("Duplicate request identifiers")
    package = Path(lean_explore.__file__).parent
    database = args.data / "lean_explore.db"
    models = json.loads(args.models.read_text())
    settings = dict(
        limit=25,
        rerank_top=25,
        bm25_k=1000,
        faiss_k=1000,
        dependency_boost=True,
        exclude_zero_bm25=False,
        seed=42,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    contract = dict(
        cases_sha256=digest(args.cases),
        runner_sha256=digest(__file__),
        models=models,
        settings=settings,
        scheduled_ids=scheduled,
        source_files_sha256={
            str(p.relative_to(package)): digest(p)
            for p in sorted(package.rglob("*.py"))
        },
        data_files_sha256={
            str(p.relative_to(args.data)): digest(p)
            for p in sorted(args.data.rglob("*"))
            if p.is_file()
        },
    )
    contract_path = args.out / "contract.json"
    journal = args.out / "records.jsonl"
    if contract_path.exists():
        if json.loads(contract_path.read_text()) != contract:
            raise ValueError("Resume inputs changed")
    elif journal.exists():
        raise ValueError("Journal exists without a contract")
    else:
        write(contract_path, contract)
        (args.out / "executed_runner.py").write_bytes(Path(__file__).read_bytes())
    done = completed_ids(journal, scheduled)
    # Local read-only lookup also records absent proposed targets explicitly.
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as conn:
        table = next(
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if row[0] in {"declarations", "declaration"}
        )
        names = {
            name: ident for ident, name in conn.execute(f"SELECT id,name FROM {table}")
        }
    targets = sorted({t for c in cases for m in c["memberships"] for t in m["targets"]})
    write(args.out / "target-availability.json", {t: names.get(t) for t in targets})

    class ObservedEngine(SearchEngine):
        observation = None

        async def _rerank(self, query, candidates, limit, trace=None):
            documents = [rerank_document(d) for d in candidates]
            response = await self.reranker_client.rerank(query, documents)
            scores = {
                "current_mixture": combine_rerank_scores(
                    query, candidates, response.scores
                ),
                "neural_only": list(response.scores),
                "without_final_dependency": combine_rerank_scores(
                    query, candidates, response.scores, RerankWeights(dependency=0.0)
                ),
            }
            rankings = {
                key: [
                    d.id
                    for d, _ in sorted(
                        zip(candidates, values), key=lambda pair: pair[1], reverse=True
                    )
                ]
                for key, values in scores.items()
            }
            # Audit true model inputs; timings therefore include instrumentation.
            tokens = [
                len(
                    self.reranker_client.tokenizer.encode(
                        self.reranker_client._format_pair(query, text),
                        add_special_tokens=True,
                    )
                )
                for text in documents
            ]
            self.observation = dict(
                candidate_ids=[d.id for d in candidates],
                scores=scores,
                rankings=rankings,
                input_tokens=tokens,
                truncated_pairs=sum(
                    n > self.reranker_client.max_length for n in tokens
                ),
            )
            ordered = sorted(
                zip(candidates, scores["current_mixture"]),
                key=lambda pair: pair[1],
                reverse=True,
            )
            record_stage(trace, "reranked", (d.id for d, _ in ordered))
            return _top_results([d for d, _ in ordered], limit, trace)

    engine = ObservedEngine(
        db_url=f"sqlite+aiosqlite:///{database}",
        data_directory=args.data,
        embedding_model_name=models["Qwen/Qwen3-Embedding-0.6B"]["path"],
        reranker_model_name=models["Qwen/Qwen3-Reranker-0.6B"]["path"],
    )
    started = time.monotonic()
    errors = 0
    try:
        await engine.search("natural number addition", limit=25, rerank_top=25)
        with journal.open("a", encoding="utf-8") as stream:
            for index, case in enumerate(cases[len(done) :], len(done)):
                trace = SearchTrace()
                engine.observation = None
                tick = time.monotonic()
                record = dict(query_id=case["id"], status="error", results=[])
                try:
                    found = await engine.search(
                        case["query"],
                        packages=case["packages"],
                        trace=trace,
                        **{k: v for k, v in settings.items() if k != "seed"},
                    )
                    record.update(
                        status="ok",
                        results=[
                            dict(id=d.id, name=d.name, module=d.module) for d in found
                        ],
                    )
                except Exception as exc:
                    errors += 1
                    record["error"] = dict(type=type(exc).__name__, message=str(exc))
                record.update(
                    latency_ms=1000 * (time.monotonic() - tick),
                    trace=dataclasses.asdict(trace),
                    fixed_pool=engine.observation,
                    exact_name_id=names.get(case["query"]),
                )
                stream.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
                )
                stream.flush()
                if (index + 1) % 25 == 0 or index + 1 == len(cases):
                    os.fsync(stream.fileno())
                    count = index + 1 - len(done)
                    elapsed = time.monotonic() - started
                    progress = dict(
                        completed=index + 1,
                        scheduled=len(cases),
                        this_session_errors=errors,
                        elapsed_seconds=elapsed,
                        seconds_per_query=elapsed / count,
                        estimated_remaining_seconds=(len(cases) - index - 1)
                        * elapsed
                        / count,
                    )
                    write(args.out / "progress.json", progress)
                    print(json.dumps(progress), flush=True)
        write(
            args.out / "complete.json",
            dict(
                scheduled=len(cases),
                completed=len(completed_ids(journal, scheduled)),
                records_sha256=digest(journal),
                contract_sha256=digest(contract_path),
                gpu=torch.cuda.get_device_name(0),
                latency_scope="Local instrumented replay, not production latency",
            ),
        )
    finally:
        await engine.engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "data", "models", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
