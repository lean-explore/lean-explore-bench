"""Run paired candidate-selection ablations on a frozen local corpus.

Usage: python -m scripts.candidate_selection --help
Inputs contain public or otherwise approved queries and judged declaration names.
Outputs omit query text, but remain private when derived from private queries.
"""

import argparse
import asyncio
import hashlib
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from lean_explore.search.engine import SearchEngine
from lean_explore.search.trace import SearchTrace


@dataclass(frozen=True)
class Variant:
    """One combination of candidate selection settings."""

    depth: int
    exclude_zero_bm25: bool
    dependency_boost: bool


def variants(limit: int) -> list[Variant]:
    """Compare legacy depth equal to limit with depths 50 and 100."""
    return [
        Variant(depth, exclude, boost)
        for depth in dict.fromkeys((limit, 50, 100))
        for exclude in (False, True)
        for boost in (True, False)
    ]


def load_queries(path: Path) -> list[dict]:
    """Validate a JSON list of query IDs, text, categories and relevant names."""
    queries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(queries, list) or not queries:
        raise ValueError("Expected a nonempty query list.")
    seen = set()
    for query in queries:
        for key in ("id", "query", "category"):
            if not isinstance(query.get(key), str) or not query[key].strip():
                raise ValueError(f"Each query needs a nonempty {key}.")
        if query["id"] in seen:
            raise ValueError(f"Duplicate query ID: {query['id']}")
        seen.add(query["id"])
        relevant = query.get("relevant")
        if (
            not isinstance(relevant, list)
            or not relevant
            or any(not isinstance(name, str) or not name.strip() for name in relevant)
        ):
            raise ValueError("Each query needs a nonempty list of relevant names.")
        if len(relevant) != len(set(relevant)):
            raise ValueError("Duplicate relevant names would distort recall.")
        packages = query.get("packages")
        if packages is not None and (
            not isinstance(packages, list)
            or any(not isinstance(package, str) for package in packages)
        ):
            raise ValueError("Packages must be a list of strings.")
    return queries


def ranking_metrics(identifiers: list[int], relevant: set[int], k: int) -> dict:
    """Measure binary relevance against known labels; unjudged is not irrelevant."""
    top = identifiers[:k]
    hits = [index for index, cid in enumerate(top, 1) if cid in relevant]
    ideal = sum(
        1 / math.log2(index + 1) for index in range(1, min(k, len(relevant)) + 1)
    )
    return {
        "hit": float(bool(hits)),
        "recall": len(hits) / len(relevant),
        "mrr": 1 / hits[0] if hits else 0.0,
        "ndcg": sum(1 / math.log2(index + 1) for index in hits) / ideal,
    }


async def resolve_targets(
    engine: SearchEngine, queries: list[dict]
) -> dict[str, set[int]]:
    """Reject corpus mismatches before running any comparison."""
    targets = {}
    for query in queries:
        identifiers = set()
        for name in query["relevant"]:
            declaration = await engine.get_by_name(name)
            if declaration is None:
                raise ValueError(
                    f"Target absent from corpus: {name} (query {query['id']})"
                )
            packages = query.get("packages")
            if packages and declaration.module.split(".")[0] not in packages:
                raise ValueError(f"Target excluded by package filter: {name}")
            identifiers.add(declaration.id)
        targets[query["id"]] = identifiers
    return targets


async def run_case(
    engine: SearchEngine,
    query: dict,
    relevant: set[int],
    variant: Variant,
    limit: int,
    retrieval_depth: int,
    repetition: int,
) -> dict:
    """Execute one measured search and locate relevant candidates at every stage."""
    trace = SearchTrace()
    started = perf_counter()
    results = await engine.search(
        query["query"],
        limit=limit,
        rerank_top=variant.depth,
        bm25_k=retrieval_depth,
        faiss_k=retrieval_depth,
        packages=query.get("packages"),
        trace=trace,
        exclude_zero_bm25=variant.exclude_zero_bm25,
        dependency_boost=variant.dependency_boost,
    )
    elapsed = (perf_counter() - started) * 1000
    return {
        "query_id": query["id"],
        "category": query["category"],
        "variant": asdict(variant),
        "repetition": repetition,
        "latency_ms": elapsed,
        "stage_elapsed_ms": trace.elapsed_ms,
        "stages": {
            stage: {
                "count": len(ids),
                "relevant_ranks": {
                    str(cid): ids.index(cid) + 1 for cid in relevant if cid in ids
                },
                **ranking_metrics(ids, relevant, max(len(ids), 1)),
            }
            for stage, ids in trace.stages.items()
        },
        "results": [result.id for result in results],
        "metrics": ranking_metrics([result.id for result in results], relevant, limit),
    }


async def run_experiment(
    engine: SearchEngine,
    queries: list[dict],
    limit: int = 10,
    retrieval_depth: int = 1000,
    repetitions: int = 1,
    seed: int = 42,
) -> list[dict]:
    """Warm models, then randomize variant order within each paired query."""
    targets = await resolve_targets(engine, queries)
    configurations = variants(limit)
    await engine.search(
        queries[0]["query"],
        limit=limit,
        rerank_top=100,
        bm25_k=retrieval_depth,
        faiss_k=retrieval_depth,
    )
    records = []
    rng = random.Random(seed)
    for repetition in range(repetitions):
        order = list(queries)
        rng.shuffle(order)
        for query in order:
            ordered = list(configurations)
            rng.shuffle(ordered)
            for variant in ordered:
                records.append(
                    await run_case(
                        engine,
                        query,
                        targets[query["id"]],
                        variant,
                        limit,
                        retrieval_depth,
                        repetition,
                    )
                )
    return records


def summarize(records: list[dict]) -> list[dict]:
    """Report per-variant overall/category means and descriptive latency quantiles."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in records:
        variant = json.dumps(row["variant"], sort_keys=True)
        for category in {row["category"], "__all__"}:
            groups.setdefault((variant, category), []).append(row)
    summaries = []
    for (variant, category), rows in sorted(groups.items()):
        latency = sorted(row["latency_ms"] for row in rows)
        summaries.append(
            {
                "variant": json.loads(variant),
                "category": category,
                "queries": len({row["query_id"] for row in rows}),
                "runs": len(rows),
                "metrics": {
                    key: statistics.mean(row["metrics"][key] for row in rows)
                    for key in ("hit", "recall", "mrr", "ndcg")
                },
                "candidate_recall": statistics.mean(
                    row["stages"].get("reranker_input", {}).get("recall", 0)
                    for row in rows
                ),
                "latency_p50_ms": statistics.median(latency),
                "latency_p95_ms": latency[math.ceil(0.95 * len(latency)) - 1],
            }
        )
    return summaries


def sha256(path: Path) -> str:
    """Hash a file without loading the corpus into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def corpus_manifest(directory: Path) -> dict[str, str]:
    """Fingerprint the database and every file used by the retrieval indices."""
    roots = [
        "lean_explore.db",
        "informalization_faiss.index",
        "informalization_faiss_ids_map.json",
        "bm25_ids_map.json",
        "bm25_name_spaced",
        "bm25_name_raw",
    ]
    files = []
    for name in roots:
        path = directory / name
        files.extend(sorted(path.rglob("*")) if path.is_dir() else [path])
    return {
        str(path.relative_to(directory)): sha256(path)
        for path in files
        if path.is_file()
    }


def parser() -> argparse.ArgumentParser:
    """Build the command line for explicit corpus and output locations."""
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--data-directory", type=Path, required=True)
    result.add_argument("--queries", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--limit", type=int, choices=(5, 10), default=10)
    result.add_argument("--retrieval-depth", type=int, default=1000)
    result.add_argument("--repetitions", type=int, default=1)
    result.add_argument("--seed", type=int, default=42)
    result.add_argument("--embedding-model", default="Qwen/Qwen3-Embedding-0.6B")
    result.add_argument("--reranker-model", default="Qwen/Qwen3-Reranker-0.6B")
    return result


def write_report(
    arguments: argparse.Namespace, manifest: dict, records: list[dict]
) -> None:
    """Write a new report without overwriting a previous run."""
    output = {
        "schema_version": 1,
        "arguments": vars(arguments),
        "query_file_sha256": sha256(arguments.queries),
        "corpus_sha256": manifest,
        "package_versions": {
            name: version(name)
            for name in ("lean-explore", "bm25s", "faiss-cpu", "torch", "transformers")
        },
        "source_sha256": {
            str(path.relative_to(Path(__file__).resolve().parents[1])): sha256(path)
            for path in [
                Path(__file__).resolve(),
                *sorted(
                    (
                        Path(__file__).resolve().parents[1] / "src/lean_explore/search"
                    ).glob("*.py")
                ),
            ]
        },
        "summary": summarize(records),
        "records": records,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x", encoding="utf-8") as destination:
        json.dump(output, destination, indent=2, default=str)


async def main(arguments: argparse.Namespace) -> None:
    """Run local experiments and write metrics plus a reproducibility manifest."""
    if arguments.repetitions < 1 or arguments.retrieval_depth < 1:
        raise ValueError("Repetitions and retrieval depth must be positive.")
    if arguments.output.exists():
        raise FileExistsError(arguments.output)
    directory = arguments.data_directory.resolve()
    database = directory / "lean_explore.db"
    if not database.is_file():
        raise FileNotFoundError(database)
    queries = load_queries(arguments.queries)
    manifest = corpus_manifest(directory)
    engine = SearchEngine(
        db_url=f"sqlite+aiosqlite:///{database}",
        data_directory=directory,
        embedding_model_name=arguments.embedding_model,
        reranker_model_name=arguments.reranker_model,
    )
    try:
        records = await run_experiment(
            engine,
            queries,
            arguments.limit,
            arguments.retrieval_depth,
            arguments.repetitions,
            arguments.seed,
        )
    finally:
        await engine.engine.dispose()
    write_report(arguments, manifest, records)


if __name__ == "__main__":
    asyncio.run(main(parser().parse_args()))
