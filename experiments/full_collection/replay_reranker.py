"""Replay a corrected production reranker over every frozen candidate pool."""

import argparse
import asyncio
import json
import math
import os
import random
import time
from pathlib import Path

from collection import digest, write
from replay_trace import normalized_trace
from run import completed_ids


async def next_record(stream, base):
    """Read one complete line, allowing the baseline producer to finish it."""
    while True:
        offset = stream.tell()
        line = stream.readline()
        if line.endswith("\n"):
            return json.loads(line)
        stream.seek(offset)
        if (base / "complete.json").exists():
            raise ValueError("Baseline ended before the frozen schedule")
        await asyncio.sleep(5)


def reranked_record(original, identifiers, scores, tokens, budget):
    """Replace only reranking fields; retain retrieval and output filtering."""
    record = dict(original)
    visible = {d["id"]: d for d in original["results"]}
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate candidates")
    if any(len(values) != len(identifiers) for values in scores.values()):
        raise ValueError("Missing scores")
    if any(not math.isfinite(s) for values in scores.values() for s in values):
        raise ValueError("Non-finite score")
    ranked = {
        method: [
            identifier
            for identifier, _ in sorted(
                zip(identifiers, values, strict=True), key=lambda p: p[1], reverse=True
            )
        ]
        for method, values in scores.items()
    }
    record["results"] = [
        visible[identifier]
        for identifier in ranked["current_mixture"]
        if identifier in visible
    ]
    if set(visible) != {d["id"] for d in record["results"]}:
        raise ValueError("Replay changed the visible candidate set")
    record["fixed_pool"] = dict(
        candidate_ids=identifiers,
        scores=scores,
        rankings=ranked,
        input_tokens=tokens,
        truncated_pairs=sum(n > budget for n in tokens),
    )
    record["trace"] = {**original["trace"], "stages": dict(original["trace"]["stages"])}
    record["trace"]["stages"]["reranked"] = ranked["current_mixture"]
    record["trace"] = normalized_trace(record["trace"], record["results"])
    return record


async def run(args):
    os.environ.update(
        OMP_NUM_THREADS="2",
        MKL_NUM_THREADS="2",
        TOKENIZERS_PARALLELISM="false",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    import lean_explore
    import numpy as np
    import torch
    from lean_explore.search.engine import RERANKER_MAX_LENGTH, SearchEngine
    from lean_explore.search.ranking import (
        RerankWeights,
        combine_rerank_scores,
        rerank_document,
    )
    from lean_explore.util.reranker_client import RerankerClient

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)

    cases = json.loads(args.cases.read_text())["cases"]
    scheduled = [c["id"] for c in cases]
    base = json.loads((args.base / "contract.json").read_text())
    if digest(args.cases) != base["cases_sha256"] or scheduled != base["scheduled_ids"]:
        raise ValueError("Cases changed")
    if (
        digest(args.data / "lean_explore.db")
        != base["data_files_sha256"]["lean_explore.db"]
    ):
        raise ValueError("Corpus changed")
    package = Path(lean_explore.__file__).parent
    contract = dict(
        cases_sha256=digest(args.cases),
        scheduled_ids=scheduled,
        runner_sha256=digest(__file__),
        base_contract_sha256=digest(args.base / "contract.json"),
        source_files_sha256={
            str(p.relative_to(package)): digest(p)
            for p in sorted(package.rglob("*.py"))
        },
        models=base["models"],
        data_files_sha256=base["data_files_sha256"],
        settings={**base["settings"], "reranker_max_length": RERANKER_MAX_LENGTH},
        scope="All requests, corrected production reranker, fixed baseline candidates and visible output set. Retrieval is reused, not rerun. Replay timings exclude retrieval.",
    )
    args.out.mkdir(parents=True, exist_ok=True)
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
    (args.out / "target-availability.json").write_bytes(
        (args.base / "target-availability.json").read_bytes()
    )
    client = RerankerClient(
        model_name=base["models"]["Qwen/Qwen3-Reranker-0.6B"]["path"],
        max_length=RERANKER_MAX_LENGTH,
        batch_size=16,
    )
    if not hasattr(client, "_token_yes_id"):
        raise ValueError("The corrected production client must be installed")
    engine = SearchEngine(
        db_url=f"sqlite+aiosqlite:///{args.data}/lean_explore.db",
        data_directory=args.data,
        reranker_client=client,
    )
    started = time.monotonic()
    try:
        with (
            (args.base / "records.jsonl").open() as source,
            journal.open("a") as output,
        ):
            for index, case in enumerate(cases):
                original = await next_record(source, args.base)
                if original["query_id"] != case["id"]:
                    raise ValueError("Baseline schedule changed")
                if index < len(done):
                    continue
                tick = time.monotonic()
                record = dict(original)
                identifiers = (original.get("fixed_pool") or {}).get(
                    "candidate_ids", []
                )
                if identifiers and original["status"] == "ok":
                    loaded = await engine._load_declarations(identifiers)
                    if set(loaded) != set(identifiers):
                        raise ValueError("Candidate missing from pinned corpus")
                    declarations = [loaded[i] for i in identifiers]
                    documents = [rerank_document(d) for d in declarations]
                    response = await client.rerank(case["query"], documents)
                    scores = {
                        "current_mixture": combine_rerank_scores(
                            case["query"], declarations, response.scores
                        ),
                        "neural_only": response.scores,
                        "without_final_dependency": combine_rerank_scores(
                            case["query"],
                            declarations,
                            response.scores,
                            RerankWeights(dependency=0),
                        ),
                    }
                    tokens = [
                        len(
                            client.tokenizer.encode(
                                client._format_pair(case["query"], text),
                                add_special_tokens=False,
                            )
                        )
                        + len(client._prefix_tokens)
                        + len(client._suffix_tokens)
                        for text in documents
                    ]
                    record = reranked_record(
                        original, identifiers, scores, tokens, client.max_length
                    )
                record["baseline_latency_ms"] = original["latency_ms"]
                record["latency_ms"] = 1000 * (time.monotonic() - tick)
                record["trace"] = normalized_trace(record["trace"], record["results"])
                output.write(json.dumps(record, separators=(",", ":")) + "\n")
                output.flush()
                if (index + 1) % 25 == 0 or index + 1 == len(cases):
                    os.fsync(output.fileno())
                    progress = dict(
                        completed=index + 1,
                        scheduled=len(cases),
                        elapsed_seconds=time.monotonic() - started,
                    )
                    write(args.out / "progress.json", progress)
                    print(json.dumps(progress), flush=True)
        while not (args.base / "complete.json").exists():
            await asyncio.sleep(5)
        completion = json.loads((args.base / "complete.json").read_text())
        if digest(args.base / "records.jsonl") != completion["records_sha256"]:
            raise ValueError("Baseline journal integrity failure")
        write(
            args.out / "complete.json",
            dict(
                scheduled=len(cases),
                completed=len(completed_ids(journal, scheduled)),
                records_sha256=digest(journal),
                contract_sha256=digest(contract_path),
                baseline_records_sha256=completion["records_sha256"],
                gpu=torch.cuda.get_device_name(0),
                latency_scope=contract["scope"],
            ),
        )
    finally:
        await engine.engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "base", "data", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
