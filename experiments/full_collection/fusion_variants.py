"""Counterfactual candidate pools built from the frozen BM25 and FAISS outputs.

Each labelled request is retrieved once per channel depth with the engine's own
calls. Several ways of filling a pool of N candidates are then compared on the
same channel outputs: the engine's rank fusion (1/rank, no constant), RRF with
the conventional constant 60, dense-weighted RRF, reserved dense/lexical slots
and single channels. No reranking runs and the engine is not modified.
"""

import argparse
import asyncio
import collections
import json
import os
import time
from pathlib import Path

from collection import digest, write
from recall_depth import labelled_cases, load_corpus, make_engine, ordered
from run import completed_ids

CHANNEL_DEPTHS = (1000, 2000)
POOLS = (50, 100, 250, 500, 1000, 2000)


def rrf(lexical, dense, constant, lexical_weight=1.0, dense_weight=1.0):
    """Engine-style rank fusion; a missing candidate ranks just past the list end."""
    lexical_rank = {c: i for i, c in enumerate(ordered(lexical), 1)}
    dense_rank = {c: i for i, c in enumerate(ordered(dense), 1)}
    missing_lexical, missing_dense = len(lexical_rank) + 1, len(dense_rank) + 1
    scores = {
        c: lexical_weight / (constant + lexical_rank.get(c, missing_lexical))
        + dense_weight / (constant + dense_rank.get(c, missing_dense))
        for c in set(lexical_rank) | set(dense_rank)
    }
    return ordered(scores)


def slots(lexical_order, dense_order, size, dense_share):
    """Fill a pool with a fixed dense share, then lexical, then remaining dense."""
    pool = list(dict.fromkeys(dense_order[: round(dense_share * size)]))
    seen = set(pool)
    for source in (lexical_order, dense_order):
        for c in source:
            if len(pool) >= size:
                return pool
            if c not in seen:
                pool.append(c)
                seen.add(c)
    return pool


VARIANTS = {
    "engine_rrf": lambda lex, den: rrf(lex, den, 0),
    "rrf_c60": lambda lex, den: rrf(lex, den, 60),
    "rrf_c60_dense2": lambda lex, den: rrf(lex, den, 60, dense_weight=2.0),
    "rrf_c0_dense2": lambda lex, den: rrf(lex, den, 0, dense_weight=2.0),
    "dense_only": lambda lex, den: ordered(den),
    "lexical_only": lambda lex, den: ordered(lex),
}
SLOT_SHARES = (0.5, 0.75, 0.9)


async def replay(args):
    import lean_explore

    cases = labelled_cases(args.cases)
    scheduled = [c["id"] for c in cases]
    package = Path(lean_explore.__file__).parent
    models = json.loads(args.models.read_text())
    contract = dict(
        cases_sha256=digest(args.cases),
        runner_sha256=digest(__file__),
        scope="Counterfactual pools from frozen channel outputs; no reranking.",
        models=models,
        settings=dict(
            channel_depths=list(CHANNEL_DEPTHS),
            pools=list(POOLS),
            variants=sorted(VARIANTS),
            slot_shares=list(SLOT_SHARES),
        ),
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
    done = completed_ids(journal, scheduled)
    names, _, _ = load_corpus(args.data / "lean_explore.db")
    engine = make_engine(args, models)
    indexes = engine.indexes
    started = time.monotonic()
    try:
        await engine.embedding_client.embed(["natural number addition"], is_query=True)
        with journal.open("a", encoding="utf-8") as stream:
            for index, case in enumerate(cases[len(done) :], len(done)):
                wanted = sorted(
                    {
                        names[t]
                        for m in case["memberships"]
                        for t in m["targets"]
                        if t in names
                    }
                )
                record = dict(query_id=case["id"], status="error")
                try:
                    response = await engine.embedding_client.embed(
                        [case["query"]], is_query=True
                    )
                    embedding = response.embeddings[0]
                    result = {}
                    for depth in CHANNEL_DEPTHS:
                        lexical = indexes.name_candidates(case["query"], depth)
                        dense = indexes.semantic_candidates(embedding, depth)
                        lexical_order, dense_order = ordered(lexical), ordered(dense)
                        pools = {}
                        for name, build in VARIANTS.items():
                            ranking = build(lexical, dense)
                            position = {c: i for i, c in enumerate(ranking, 1)}
                            pools[name] = {
                                str(n): [
                                    t for t in wanted if position.get(t, n + 1) <= n
                                ]
                                for n in POOLS
                            }
                        for share in SLOT_SHARES:
                            by_size = {}
                            for n in POOLS:
                                pool = set(slots(lexical_order, dense_order, n, share))
                                by_size[str(n)] = [t for t in wanted if t in pool]
                            pools[f"slots_dense{int(100 * share)}"] = by_size
                        result[str(depth)] = pools
                    record.update(status="ok", pools=result)
                except Exception as exc:
                    record["error"] = dict(type=type(exc).__name__, message=str(exc))
                stream.write(json.dumps(record, separators=(",", ":")) + "\n")
                stream.flush()
                if (index + 1) % 100 == 0 or index + 1 == len(cases):
                    os.fsync(stream.fileno())
                    print(
                        json.dumps(
                            dict(
                                completed=index + 1, elapsed=time.monotonic() - started
                            )
                        ),
                        flush=True,
                    )
        write(
            args.out / "complete.json",
            dict(
                scheduled=len(cases),
                completed=len(completed_ids(journal, scheduled)),
                records_sha256=digest(journal),
                contract_sha256=digest(contract_path),
            ),
        )
    finally:
        await engine.engine.dispose()


def summarise(args):
    """Recall of each pool by source and by query form, absent targets in the denominator."""
    cases = labelled_cases(args.cases)
    availability = json.loads(
        (args.base / "target-availability.json").read_text(encoding="utf-8")
    )
    records = {}
    with (args.out / "records.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            records[record["query_id"]] = record
    sums = collections.defaultdict(float)
    counts = collections.Counter()
    for case in cases:
        record = records[case["id"]]
        for membership in case["memberships"]:
            if not membership["targets"]:
                continue
            targets = list(dict.fromkeys(membership["targets"]))
            groups = (
                ("source", membership["source"]),
                ("form", f"{membership['source']}/{case['categories']['form']}"),
            )
            for group in groups:
                counts[group] += 1
            if record["status"] != "ok":
                continue
            for depth, pools in record["pools"].items():
                for variant, by_size in pools.items():
                    for size, found in by_size.items():
                        found = set(found)
                        hit = sum(availability.get(t) in found for t in targets)
                        for group in groups:
                            sums[group, depth, variant, size] += hit / len(targets)
    table = collections.defaultdict(dict)
    for (group, depth, variant, size), value in sums.items():
        table[f"{group[0]}:{group[1]}"][f"{depth}/{variant}@{size}"] = (
            value / counts[group]
        )
    write(
        args.summary,
        dict(
            memberships={f"{g[0]}:{g[1]}": n for g, n in counts.items()}, recall=table
        ),
    )


def main():
    os.environ.update(
        OMP_NUM_THREADS="4",
        MKL_NUM_THREADS="4",
        TOKENIZERS_PARALLELISM="false",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "data", "models", "out", "base"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    if args.summary:
        summarise(args)
    else:
        asyncio.run(replay(args))


if __name__ == "__main__":
    main()
