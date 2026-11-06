"""Replay external development cases with stage traces and fixed-pool scores."""

import argparse
import asyncio
import dataclasses
import hashlib
import json
import os
import random
import time
from pathlib import Path


def file_hash(path):
    """Hash an input without loading it into memory."""
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def write_json(path, value):
    """Replace a checkpoint only after its complete JSON has been written."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


async def run(args):
    """Preserve scheduled requests and retain failures in external output."""
    dataset = json.loads(args.cases.read_text(encoding="utf-8-sig"))
    cases = dataset["cases"]
    if not cases or any(c.get("split") != "development" for c in cases):
        raise ValueError("Require explicit development-only cases")
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case identifiers")
    if any(
        not isinstance(c.get("query"), str) or not c["query"].strip() for c in cases
    ):
        raise ValueError("Require nonempty query text")
    destination = args.out.resolve()
    if any((p / ".git").exists() for p in (destination, *destination.parents)):
        raise ValueError("Write measured outputs outside Git checkouts")
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "executed_runner.py").write_bytes(Path(__file__).read_bytes())
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
    models = json.loads(args.models.read_text(encoding="utf-8"))
    for model in models.values():
        if not Path(model["path"]).is_dir():
            raise ValueError("Require local model snapshots")
    database = args.data / "lean_explore.db"
    if dataset["corpus_revision"] != "sha256:" + file_hash(database):
        raise ValueError("Case corpus revision differs from the database")
    package = Path(lean_explore.__file__).parent
    result = {
        "schema_version": 1,
        "corpus_revision": dataset["corpus_revision"],
        "cases_sha256": file_hash(args.cases),
        "models": models,
        "source_files_sha256": {
            str(p.relative_to(package)): file_hash(p)
            for p in sorted(package.rglob("*.py"))
        },
        "data_files_sha256": {
            str(p.relative_to(args.data)): file_hash(p)
            for p in sorted(args.data.rglob("*"))
            if p.is_file()
        },
        "runner_sha256": file_hash(Path(__file__)),
        "settings": {
            "limit": 10,
            "rerank_top": 10,
            "bm25_k": 1000,
            "faiss_k": 1000,
            "dependency_boost": True,
            "exclude_zero_bm25": False,
            "seed": 42,
            "concurrency": 1,
            "retries": 0,
        },
        "scheduled_ids": [c["id"] for c in cases],
        "records": [],
        "state": "initializing",
        "target_availability": {},
    }
    write_json(destination / "replay.json", result)

    class ObservedEngine(SearchEngine):
        """Capture the scores supplied to the existing final mixture."""

        pair_observation = None

        async def _rerank(self, query, candidates, limit, trace=None):
            documents = [rerank_document(d) for d in candidates]
            client = self.reranker_client
            response = await client.rerank(query, documents)
            scores = {
                "current_mixture": combine_rerank_scores(
                    query, candidates, response.scores
                ),
                "without_final_dependency": combine_rerank_scores(
                    query, candidates, response.scores, RerankWeights(dependency=0.0)
                ),
                "neural_only": list(response.scores),
            }
            audit = []
            for d, text in zip(candidates, documents):
                pair = client._format_pair(query, text)
                tokens = len(client.tokenizer.encode(pair, add_special_tokens=True))
                audit.append(
                    {
                        "name": d.name,
                        "pair_sha256": hashlib.sha256(pair.encode()).hexdigest(),
                        "tokens": tokens,
                        "truncated": tokens > client.max_length,
                    }
                )
            self.pair_observation = {
                "candidate_names": [d.name for d in candidates],
                "scores": scores,
                "input_audit": audit,
                "rankings": {
                    key: [
                        d.name
                        for d, _ in sorted(
                            zip(candidates, values),
                            key=lambda pair: pair[1],
                            reverse=True,
                        )
                    ]
                    for key, values in scores.items()
                },
            }
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
    try:
        await engine.search("natural number addition", limit=10, rerank_top=10)
        for target in sorted({t for c in cases for t in c.get("targets", [])}):
            declaration = await engine.get_by_name(target)
            result["target_availability"][target] = (
                None
                if declaration is None
                else {"id": declaration.id, "name": declaration.name}
            )
        result["state"] = "running"
        for case in cases:
            trace = SearchTrace()
            engine.pair_observation = None
            started = time.perf_counter()
            record = {"query_id": case["id"], "status": "error", "results": []}
            try:
                found = await engine.search(
                    case["query"],
                    limit=10,
                    rerank_top=10,
                    bm25_k=1000,
                    faiss_k=1000,
                    dependency_boost=True,
                    exclude_zero_bm25=False,
                    trace=trace,
                )
                exact = await engine.get_by_name(case["query"])
                record.update(
                    status="ok",
                    results=[d.model_dump() for d in found],
                    exact_name_result=None if exact is None else exact.name,
                )
            except Exception as error:
                record["error"] = {"type": type(error).__name__, "message": str(error)}
            record.update(
                latency_ms=(time.perf_counter() - started) * 1000,
                trace=dataclasses.asdict(trace),
                fixed_pool=engine.pair_observation,
            )
            result["records"].append(record)
            write_json(destination / "replay.json", result)
        result["runtime"] = {
            "embedding_dtype": str(
                next(engine.embedding_client.model.parameters()).dtype
            ),
            "reranker_dtype": str(
                next(engine.reranker_client.model.parameters()).dtype
            ),
            "embedding_max_tokens": engine.embedding_client.model.max_seq_length,
            "reranker_max_tokens": engine.reranker_client.max_length,
            "embedding_query_prompt": engine.embedding_client.model.prompts.get(
                "query"
            ),
            "nprobe": engine.indexes.faiss_index.nprobe,
            "latency_scope": (
                "Includes tracing, input inspection and exact-name lookup; "
                "not serving latency."
            ),
        }
        result["state"] = "complete"
    finally:
        await engine.engine.dispose()
        write_json(destination / "replay.json", result)
    print(
        json.dumps(
            {
                "scheduled": len(cases),
                "ok": sum(r["status"] == "ok" for r in result["records"]),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("cases", "data", "models", "out"):
        parser.add_argument("--" + flag, type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
