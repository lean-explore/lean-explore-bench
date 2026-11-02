"""Offline retrieval metrics and paired inference on independent task groups."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from typing import Any

Json = dict[str, Any]


def validate(collection: Json, run: Json) -> None:
    """Refuse ambiguous or incomparable inputs before producing a score."""
    revision = collection.get("corpus_revision")
    if not isinstance(revision, str) or not revision:
        raise ValueError("Collection requires a pinned corpus_revision")
    if run.get("corpus_revision") != revision:
        raise ValueError("Corpus revisions differ; evaluate coverage separately")
    if type(run.get("max_k")) is not int or run["max_k"] < 1:
        raise ValueError("Run requires a positive integer max_k")
    queries = collection.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("Collection requires nonempty queries")
    ids = set()
    for q in queries:
        if not isinstance(q, dict):
            raise ValueError("Query must be an object")
        if any(not isinstance(q.get(k), str) or not q[k] for k in ("id", "group_id")):
            raise ValueError("Query requires id and independent-task group_id")
        if q["id"] in ids:
            raise ValueError("Duplicate query id")
        ids.add(q["id"])
        if q.get("track") not in {"human", "agent", "unknown"}:
            raise ValueError("Track must be human, agent, or unknown")
        if q.get("answerability") not in {"answerable", "unanswerable", "unknown"}:
            raise ValueError("Invalid answerability")
        judgments = q.get("judgments")
        if not isinstance(judgments, dict) or any(
            not isinstance(doc, str)
            or not doc
            or type(grade) is not int
            or grade not in range(4)
            for doc, grade in judgments.items()
        ):
            raise ValueError("Judgments require document IDs and integer grades 0..3")
        relevant = any(grade >= 2 for grade in judgments.values())
        if q["answerability"] == "answerable" and not relevant:
            raise ValueError("Answerable query needs at least one grade >= 2")
        if q["answerability"] == "unanswerable" and relevant:
            raise ValueError("Unanswerable query cannot have a relevant judgment")
        routes = q.get("premise_routes", [])
        if not isinstance(routes, list) or any(
            not isinstance(route, list)
            or not route
            or any(
                not isinstance(group, list)
                or not group
                or any(
                    not isinstance(doc, str) or judgments.get(doc, 0) < 2
                    for doc in group
                )
                for group in route
            )
            for route in routes
        ):
            raise ValueError("Premise routes need nonempty groups of relevant IDs")
    results = run.get("results")
    if not isinstance(results, dict) or set(results) - ids:
        raise ValueError("Run results must be keyed by collection query IDs")
    for result in results.values():
        if not isinstance(result, dict):
            raise ValueError("Result must be an object")
        if result.get("status") not in {"ok", "error", "timeout"}:
            raise ValueError("Result requires status ok/error/timeout")
        docs = result.get("documents")
        if not isinstance(docs, list) or any(
            not isinstance(d, str) or not d for d in docs
        ):
            raise ValueError("Documents must be ranked document IDs")
        if len(docs) > run["max_k"]:
            raise ValueError("Result exceeds declared max_k")
        if result["status"] != "ok" and docs:
            raise ValueError("Failed requests cannot contain scored documents")
        if type(result.get("abstained", False)) is not bool:
            raise ValueError("abstained must be a boolean")
        if result.get("abstained") and (docs or result["status"] != "ok"):
            raise ValueError(
                "Abstention must be a successful response without documents"
            )
        for field in ("latency_ms", "cost_usd"):
            value = result.get(field)
            if value is not None and (
                type(value) not in (float, int) or not math.isfinite(value) or value < 0
            ):
                raise ValueError(f"Invalid {field}")


def ranking_metrics(
    ranked: list[str], judgments: dict[str, int], k: int
) -> dict[str, float]:
    """Score distinct documents with linear nDCG gain and binary grade >= 2.

    Duplicates consume their original rank but never earn a second gain.
    Unjudged documents have zero gain; judged@k exposes incomplete assessment.
    AP@k divides by min(k, number of known relevant documents).
    """
    if k < 1:
        raise ValueError("k must be positive")
    relevant = {doc for doc, grade in judgments.items() if grade >= 2}
    if not relevant:
        raise ValueError("Ranking metrics need a known relevant document")
    seen: set[str] = set()
    hits = 0
    rr = ap = dcg = judged = 0.0
    for rank, doc in enumerate(ranked[:k], 1):
        if doc in seen:
            continue
        seen.add(doc)
        judged += doc in judgments
        grade = judgments.get(doc, 0)
        dcg += grade / math.log2(rank + 1)
        if doc in relevant:
            hits += 1
            ap += hits / rank
            if not rr:
                rr = 1 / rank
    ideal = sum(
        grade / math.log2(rank + 1)
        for rank, grade in enumerate(sorted(judgments.values(), reverse=True)[:k], 1)
    )
    return {
        f"ndcg@{k}": dcg / ideal,
        f"recall@{k}": hits / len(relevant),
        f"success@{k}": float(hits > 0),
        f"mrr@{k}": rr,
        f"map@{k}": ap / min(k, len(relevant)),
        f"precision@{k}": hits / k,
        f"judged@{k}": judged / k,
    }


def premise_metrics(ranked: list[str], routes: list[list[list[str]]], k: int) -> Json:
    """Score interchangeable premises within alternative complete proof routes."""
    found = set(ranked[:k])
    fractions = [
        sum(bool(found.intersection(group)) for group in route) / len(route)
        for route in routes
    ]
    return {
        f"best_route_group_recall@{k}": max(fractions),
        f"route_covered@{k}": float(any(f == 1 for f in fractions)),
    }


def quantile(values: list[float], p: float) -> float | None:
    """Linear-interpolated sample quantile, absent for an empty sample."""
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    low = math.floor(index)
    high = math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def evaluate(collection: Json, run: Json, cutoffs: tuple[int, ...]) -> Json:
    """Evaluate every scheduled query; missing requests count as failures.

    Unknown answerability is excluded from relevance scores, never scored as
    zero. Known unanswerable queries are evaluated for explicit abstention.
    Cutoffs beyond an engine's declared limit are unavailable, not flat curves.
    """
    validate(collection, run)
    if not cutoffs or any(type(k) is not int or k < 1 for k in cutoffs):
        raise ValueError("Cutoffs must be positive integers")
    per_query = []
    for q in collection["queries"]:
        result = run["results"].get(q["id"], {"status": "missing", "documents": []})
        ranked = result["documents"]
        ok = result["status"] == "ok"
        abstained = result.get("abstained", False) and ok
        scores: Json = {"request_success": float(ok)}
        if q["answerability"] == "answerable":
            for k in cutoffs:
                if k <= run["max_k"]:
                    scores.update(ranking_metrics(ranked, q["judgments"], k))
                    if q.get("premise_routes"):
                        scores.update(premise_metrics(ranked, q["premise_routes"], k))
            scores["false_abstention"] = float(abstained)
        elif q["answerability"] == "unanswerable":
            scores["correct_abstention"] = float(abstained)
            scores["false_return"] = float(bool(ranked))
        per_query.append(
            {
                "id": q["id"],
                "group_id": q["group_id"],
                "track": q["track"],
                "answerability": q["answerability"],
                "status": result["status"],
                "scores": scores,
                "latency_ms": result.get("latency_ms"),
                "cost_usd": result.get("cost_usd"),
            }
        )
    summaries = {}
    for track in ("all", "human", "agent", "unknown"):
        rows = [r for r in per_query if track == "all" or r["track"] == track]
        if not rows:
            continue
        names = sorted({name for r in rows for name in r["scores"]})
        metrics = {}
        for name in names:
            values = [r["scores"][name] for r in rows if name in r["scores"]]
            metrics[name] = {"mean": statistics.mean(values), "n": len(values)}
        latency = [float(r["latency_ms"]) for r in rows if r["latency_ms"] is not None]
        cost = [float(r["cost_usd"]) for r in rows if r["cost_usd"] is not None]
        summaries[track] = {
            "scheduled": len(rows),
            "independent_groups": len({r["group_id"] for r in rows}),
            "metrics": metrics,
            "latency_ms": {
                "n": len(latency),
                "p50": quantile(latency, 0.5),
                "p95": quantile(latency, 0.95),
                "p99": quantile(latency, 0.99),
            },
            "cost_usd": {"n": len(cost), "total": sum(cost) if cost else None},
        }
    return {
        "run_name": run.get("name", "unnamed"),
        "run_sha256": hashlib.sha256(
            json.dumps(run, sort_keys=True, ensure_ascii=True).encode()
        ).hexdigest(),
        "collection_sha256": hashlib.sha256(
            json.dumps(collection, sort_keys=True, ensure_ascii=True).encode()
        ).hexdigest(),
        "corpus_revision": collection["corpus_revision"],
        "gain": "linear",
        "binary_relevance_threshold": 2,
        "unavailable_cutoffs": [k for k in cutoffs if k > run["max_k"]],
        "summary": summaries,
        "per_query": per_query,
    }


def compare(
    baseline: Json,
    candidate: Json,
    metric: str,
    track: str = "all",
    seed: int = 42,
    samples: int = 10000,
) -> Json:
    """Paired cluster bootstrap CI and group sign-randomization p-value.

    Groups are independent tasks/target families, not individual paraphrases.
    Confidence intervals describe the mean query-score difference. The test
    flips all differences in one group together. One prespecified comparison
    is returned; use Holm correction if several comparisons are selected.
    """
    if samples < 100:
        raise ValueError("Use at least 100 resamples")
    if baseline["corpus_revision"] != candidate["corpus_revision"]:
        raise ValueError("Corpus revisions differ")
    if baseline["collection_sha256"] != candidate["collection_sha256"]:
        raise ValueError("Collection or relevance judgments differ")
    left = {r["id"]: r for r in baseline["per_query"]}
    right = {r["id"]: r for r in candidate["per_query"]}
    if left.keys() != right.keys():
        raise ValueError("Comparison needs the same scheduled queries")
    groups: dict[str, list[float]] = defaultdict(list)
    for qid, a in left.items():
        b = right[qid]
        if any(a[key] != b[key] for key in ("track", "group_id", "answerability")):
            raise ValueError("Query metadata differs")
        if track != "all" and a["track"] != track:
            continue
        if (metric in a["scores"]) != (metric in b["scores"]):
            raise ValueError("Metric coverage differs between runs")
        if metric in a["scores"]:
            groups[a["group_id"]].append(b["scores"][metric] - a["scores"][metric])
    if len(groups) < 2:
        raise ValueError(
            "At least two independent groups with this metric are required"
        )
    values = list(groups.values())
    n = sum(len(v) for v in values)
    observed = sum(map(sum, values)) / n
    rng = random.Random(seed)
    boot = []
    for _ in range(samples):
        chosen = rng.choices(values, k=len(values))
        boot.append(sum(map(sum, chosen)) / sum(len(v) for v in chosen))
    extreme = 0
    for _ in range(samples):
        statistic = sum(rng.choice((-1, 1)) * sum(v) for v in values) / n
        extreme += abs(statistic) >= abs(observed) - 1e-15
    return {
        "baseline": baseline["run_name"],
        "candidate": candidate["run_name"],
        "baseline_sha256": baseline["run_sha256"],
        "candidate_sha256": candidate["run_sha256"],
        "collection_sha256": baseline["collection_sha256"],
        "metric": metric,
        "track": track,
        "n_queries": n,
        "n_groups": len(values),
        "candidate_minus_baseline": observed,
        "cluster_bootstrap_ci95": [quantile(boot, 0.025), quantile(boot, 0.975)],
        "paired_group_randomization_p": (extreme + 1) / (samples + 1),
        "samples": samples,
        "seed": seed,
        "multiple_comparisons_adjusted": False,
    }


def holm(p_values: list[float]) -> list[float]:
    """Holm-adjust a prespecified family of p-values, retaining input order."""
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in p_values):
        raise ValueError("Invalid p-value")
    result = [0.0] * len(p_values)
    previous = 0.0
    for rank, index in enumerate(
        sorted(range(len(p_values)), key=p_values.__getitem__)
    ):
        previous = max(previous, min(1.0, (len(p_values) - rank) * p_values[index]))
        result[index] = previous
    return result
