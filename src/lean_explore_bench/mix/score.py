"""Score an engine run on the query mix, by bucket and by library.

Scoring is done by ``lean_explore_bench.evaluate``. This module only groups
its per-query scores: one row per query type and one per library.
"""

import statistics
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from lean_explore_bench.evaluate import evaluate

from lean_explore_bench.mix.assemble import to_collection
from lean_explore_bench.mix.forms import classify
from lean_explore_bench.mix.record import QueryRecord
from lean_explore_bench.mix.spec import BUCKET_OF_FORM, THREAD_BUCKET

HOSTED_REVISION = "hosted-index-not-pinned"
"""Corpus label for runs against a hosted engine, whose snapshot is unknown."""


def metric_names(limit: int) -> list[str]:
    """Return the reported metrics for runs with ``limit`` results per query."""
    names = ["success@1", f"success@{limit}", f"mrr@{limit}", f"ndcg@{limit}"]
    return list(dict.fromkeys(names))


def _mean_rows(
    per_query: list[dict[str, Any]], key_of: dict[str, str], metrics: list[str]
) -> dict[str, dict[str, float]]:
    """Average each metric over the queries that share a key."""
    grouped: dict[str, list[dict[str, float]]] = defaultdict(list)
    for row in per_query:
        grouped[key_of[row["id"]]].append(row["scores"])
    return {
        key: {
            "queries": len(scores),
            "request_success": statistics.mean(s["request_success"] for s in scores),
            **{
                metric: statistics.mean(s[metric] for s in scores) for metric in metrics
            },
        }
        for key, scores in sorted(grouped.items())
    }


def score(
    records: Iterable[QueryRecord],
    results: dict[str, dict[str, Any]],
    engine: str,
    split: str = "all",
    limit: int = 10,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Score one engine's results.

    Args:
        records: The queries of the mix.
        results: The engine's result for each query, from
            :func:`lean_explore_bench.mix.engines.read_results`. A query
            without a result counts as a failed request.
        engine: Engine name, recorded in the report.
        split: ``development``, ``test`` or ``all``.
        limit: Results requested per query when the run was made.
        weights: Share of real searches in each form. When given, the report
            also holds a traffic-weighted score: the mean score of each form
            (every query is sorted by :func:`forms.classify`), weighted by
            that form's share of real searches. Zulip questions are left
            out of it, because they are not written like search queries.

    Returns:
        A report with mean scores overall, by query type and by library.
    """
    chosen = [
        QueryRecord.from_json({**record.to_json(), "split": "scored"})
        for record in records
        if split == "all" or record.split == split
    ]
    collection = to_collection(chosen, HOSTED_REVISION, "scored")
    run = {
        "name": engine,
        "corpus_revision": HOSTED_REVISION,
        "max_k": limit,
        "results": {
            record.id: {
                "status": results[record.id]["status"],
                "documents": results[record.id]["documents"][:limit],
                "latency_ms": results[record.id].get("latency_ms"),
            }
            for record in chosen
            if record.id in results
        },
    }
    evaluated = evaluate(collection, run, tuple(sorted({1, limit})))
    per_query = evaluated["per_query"]
    metrics = metric_names(limit)

    def rows(key_of: dict[str, str]) -> dict[str, dict[str, float]]:
        return _mean_rows(per_query, key_of, metrics)

    written = {
        record.id: classify(record.query)
        for record in chosen
        if record.source == "declaration"
    }
    by_form = _mean_rows(
        [row for row in per_query if row["id"] in written], written, metrics
    )
    weighted = None
    if weights is not None:
        present = {form: share for form, share in weights.items() if form in by_form}
        total = sum(present.values())
        weighted = {
            metric: sum(
                by_form[form][metric] * share for form, share in present.items()
            )
            / total
            for metric in metrics
        }
    return {
        "engine": engine,
        "split": split,
        "by_form": by_form,
        "traffic_weighted": weighted,
        "corpus_revision": HOSTED_REVISION,
        "collection_sha256": evaluated["collection_sha256"],
        "metrics": metrics,
        "overall": rows({record.id: "all" for record in chosen})["all"],
        "by_query_type": rows({record.id: record.query_type for record in chosen}),
        "by_library": rows({record.id: record.library for record in chosen}),
        "by_source": rows({record.id: record.source for record in chosen}),
        "by_bucket": (by_bucket := rows({r.id: bucket_of(r) for r in chosen})),
        "benchmark": {
            metric: sum(values[metric] for values in by_bucket.values())
            / len(by_bucket)
            for metric in metrics
        },
        "by_type_and_library": rows(
            {record.id: f"{record.query_type} / {record.library}" for record in chosen}
        ),
    }


def bucket_of(record: QueryRecord) -> str:
    """Bucket of a record: thread queries form one, written ones go by form."""
    if record.source != "declaration":
        return THREAD_BUCKET
    return BUCKET_OF_FORM.get(record.query_type, record.query_type)


def _matrix(report: dict[str, Any], metric: str) -> list[str]:
    """Render one metric by query type (rows) and library (columns).

    Engines index different libraries, so a bucket's score mixes libraries
    an engine covers with ones it does not. Each cell shows the score and,
    in brackets, the number of queries.
    """
    cells = {
        tuple(key.split(" / ")): values
        for key, values in report["by_type_and_library"].items()
    }
    types = sorted({query_type for query_type, _ in cells})
    libraries = sorted({library for _, library in cells})
    lines = [
        f"| {metric} by query type and library | " + " | ".join(libraries) + " |",
        "| --- | " + " | ".join("---:" for _ in libraries) + " |",
    ]
    for query_type in types:
        row = [
            f"{cells[(query_type, library)][metric]:.2f} "
            f"({cells[(query_type, library)]['queries']})"
            if (query_type, library) in cells
            else ""
            for library in libraries
        ]
        lines.append(f"| {query_type} | " + " | ".join(row) + " |")
    return [*lines, ""]


def render(report: dict[str, Any]) -> str:
    """Render a report as Markdown tables."""
    metrics = report["metrics"]
    header = "| {} | Queries | " + " | ".join(metrics) + " |"
    rule = "| --- | ---: | " + " | ".join("---:" for _ in metrics) + " |"

    def row(label: str, values: dict[str, float]) -> str:
        cells = " | ".join(f"{values[metric]:.3f}" for metric in metrics)
        return f"| {label} | {values['queries']} | {cells} |"

    lines = [f"### {report['engine']} ({report['split']} queries)", ""]
    for title, section in (
        ("Query type", "by_query_type"),
        ("Library", "by_library"),
        ("Source", "by_source"),
        ("Bucket", "by_bucket"),
    ):
        lines += [header.format(title), rule]
        lines += [row(label, values) for label, values in report[section].items()]
        lines += [row("**All**", report["overall"]), ""]
    cells = ", ".join(
        f"{metric} {report['benchmark'][metric]:.3f}" for metric in metrics
    )
    lines += [f"Benchmark score (mean of the buckets): {cells}", ""]
    lines += _matrix(report, f"success@{metrics[-1].rsplit('@', 1)[-1]}")
    if report["traffic_weighted"] is not None:
        cells = ", ".join(
            f"{metric} {report['traffic_weighted'][metric]:.3f}" for metric in metrics
        )
        lines += [f"Weighted by real traffic: {cells}", ""]
    return "\n".join(lines)
