"""Reconstruct source/category results without treating missing labels as negatives."""

import argparse
import collections
import json
import math
from pathlib import Path

from collection import digest, write

STAGES = {
    "lexical": "bm25",
    "dense": "semantic",
    "fusion": "fusion",
    "selection": "selection",
}
CONFIGS = [
    *STAGES,
    "pre_rerank_same_pool",
    "current_mixture",
    "neural_only",
    "without_final_dependency",
]


def metrics(ranking, targets, routes=(), cutoffs=(1, 5, 10, 25)):
    """Score known targets; empty relevance is unavailable, never a zero score."""
    if not targets:
        return {}
    if len(ranking) != len(set(ranking)):
        raise ValueError("Duplicate returned documents")
    result = {}
    for k in cutoffs:
        found = set(ranking[:k]) & targets
        dcg = sum(
            1 / math.log2(i + 2) for i, d in enumerate(ranking[:k]) if d in targets
        )
        ideal = sum(1 / math.log2(i + 2) for i in range(min(len(targets), k)))
        result.update(
            {
                f"success@{k}": float(bool(found)),
                f"recall@{k}": len(found) / len(targets),
                f"ndcg@{k}": dcg / ideal,
                f"mrr@{k}": next(
                    (1 / (i + 1) for i, d in enumerate(ranking[:k]) if d in targets),
                    0.0,
                ),
            }
        )
        if routes:
            result[f"complete_route@{k}"] = float(
                any(set(route) <= set(ranking[:k]) for route in routes if route)
            )
    return result


def rankings(record):
    if record["status"] != "ok":
        return {name: [] for name in CONFIGS}
    trace = record["trace"]["stages"]
    pool = record.get("fixed_pool") or {}
    visible = {d["id"] for d in record["results"]}
    return {
        **{name: trace.get(stage, []) for name, stage in STAGES.items()},
        "pre_rerank_same_pool": [
            d for d in pool.get("candidate_ids", []) if d in visible
        ],
        "current_mixture": [d["id"] for d in record["results"]],
        "neural_only": [
            d for d in pool.get("rankings", {}).get("neural_only", []) if d in visible
        ],
        "without_final_dependency": [
            d
            for d in pool.get("rankings", {}).get("without_final_dependency", [])
            if d in visible
        ],
    }


def add(bucket, record, ranked, targets, routes):
    bucket["requests"] += 1
    bucket["errors"] += record["status"] != "ok"
    bucket["empty_results"] += not record["results"]
    bucket["results_sum"] += len(record["results"])
    bucket["latency_ms_sum"] += record["latency_ms"]
    pool = record.get("fixed_pool") or {}
    bucket["truncated_pairs"] += pool.get("truncated_pairs", 0)
    bucket["reranked_pairs"] += len(pool.get("candidate_ids", []))
    before = ranked["pre_rerank_same_pool"]
    after = ranked["current_mixture"]
    bucket["top1_changed"] += bool(before and after and before[0] != after[0])
    bucket["labelled_requests"] += bool(targets)
    for config, ranking in ranked.items():
        cutoffs = (1, 5, 10, 25, 100, 1000) if config in STAGES else (1, 5, 10, 25)
        for metric, value in metrics(ranking, targets, routes, cutoffs).items():
            bucket["sums"][config][metric] += value


def fresh():
    return dict(
        requests=0,
        errors=0,
        empty_results=0,
        results_sum=0,
        latency_ms_sum=0.0,
        truncated_pairs=0,
        reranked_pairs=0,
        top1_changed=0,
        labelled_requests=0,
        sums=collections.defaultdict(lambda: collections.defaultdict(float)),
    )


def finish(bucket):
    n = bucket["labelled_requests"]
    return {
        **{k: v for k, v in bucket.items() if k not in {"sums", "latency_ms_sum"}},
        "latency_ms_mean": bucket["latency_ms_sum"] / bucket["requests"],
        "metrics": {
            c: {k: v / n for k, v in values.items()}
            for c, values in bucket["sums"].items()
        }
        if n
        else None,
    }


def score(args):
    cases = json.loads(args.cases.read_text())["cases"]
    inventory = json.loads(args.cases.with_name("inventory.json").read_text())
    contract = json.loads((args.run / "contract.json").read_text())
    completion = json.loads((args.run / "complete.json").read_text())
    if digest(args.cases) != contract["cases_sha256"] or completion[
        "records_sha256"
    ] != digest(args.run / "records.jsonl"):
        raise ValueError("Input integrity mismatch")
    if completion["contract_sha256"] != digest(args.run / "contract.json"):
        raise ValueError("Contract changed")
    if completion["completed"] != len(cases) or completion["scheduled"] != len(cases):
        raise ValueError("Incomplete execution")
    availability = json.loads((args.run / "target-availability.json").read_text())
    totals = collections.defaultdict(fresh)
    source_unique = collections.defaultdict(set)
    absent = collections.defaultdict(set)
    all_ops = fresh()
    query_rows = []
    with (args.run / "records.jsonl").open() as stream:
        count = 0
        for case, line in zip(cases, stream, strict=True):
            record = json.loads(line)
            if (
                record["query_id"] != case["id"]
                or contract["scheduled_ids"][count] != case["id"]
            ):
                raise ValueError("Missing, reordered or duplicate query")
            count += 1
            ranked = rankings(record)
            add(all_ops, record, ranked, set(), [])
            for membership in case["memberships"]:
                source = membership["source"]
                source_unique[source].add(case["id"])
                kind = membership["label_kind"]
                # Absent target sentinels retain denominator without matching a result.
                targets = {
                    availability[t]
                    if availability.get(t) is not None
                    else "absent:" + t
                    for t in membership["targets"]
                }
                routes = [
                    [
                        availability[t]
                        if availability.get(t) is not None
                        else "absent:" + t
                        for t in route
                    ]
                    for route in membership.get("routes", [])
                ]
                absent[source].update(
                    t for t in membership["targets"] if availability.get(t) is None
                )
                slices = [
                    ("all", "all"),
                    *[
                        (axis, case["categories"][axis])
                        for axis in ("form", "surface", "intent_cue", "domain_cue")
                    ],
                ]
                for axis in (
                    "channel",
                    "upstream_style",
                    "difficulty",
                    "original_form",
                    "original_intent",
                    "original_domain",
                ):
                    if membership.get(axis):
                        slices.append((axis, membership[axis]))
                for tag in sorted(set(membership.get("domain_tags", []))):
                    slices.append(("upstream_domain", tag))
                if targets and all(isinstance(t, int) for t in targets):
                    slices.append(("target_availability", "all_targets_present"))
                for axis, label in slices:
                    add(
                        totals[source, kind, axis, label],
                        record,
                        ranked,
                        targets,
                        routes,
                    )
                query_rows.append(
                    dict(
                        query_id=case["id"],
                        source=source,
                        source_id=membership["source_id"],
                        group=membership.get("group", membership["source_id"]),
                        upstream_style=membership.get("upstream_style"),
                        label_kind=kind,
                        form=case["categories"]["form"],
                        status=record["status"],
                        target_count=len(targets),
                        present_targets=sum(isinstance(t, int) for t in targets),
                        metrics={
                            c: metrics(r, targets, routes) for c, r in ranked.items()
                        }
                        if targets
                        else None,
                    )
                )
    args.out.mkdir(parents=True, exist_ok=False)
    with (args.out / "per-query.jsonl").open("w") as stream:
        for row in query_rows:
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")
    summary = dict(
        scope="full-available-collection-v1",
        execution_scope=contract.get(
            "scope", "End-to-end instrumented baseline replay."
        ),
        inventory=inventory,
        operation=finish(all_ops),
        settings=contract["settings"],
        sources={
            s: dict(distinct_requests=len(ids), absent_target_names=len(absent[s]))
            for s, ids in source_unique.items()
        },
        slices=[
            dict(source=s, label_kind=k, axis=a, category=v, **finish(b))
            for (s, k, a, v), b in sorted(totals.items())
        ],
        limitations=[
            "No relevance labels for usage logs or FATE-H retrieval diagnostics.",
            "Discussion reply links are candidate-answer proxies, not verified relevance.",
            "Historical pilot targets are proposals; existing human judgments remain in the earlier release.",
            "Forms are rule-based; intent and domain cues are unvalidated.",
            "Full available collection, not a fresh held-out test or a representative sample of all Lean users.",
            "Pinned local engine, models and corpus; instrumented timing is not production latency.",
            "No global relevance score mixes different label types.",
        ],
    )
    write(args.out / "summary.json", summary)
    print(json.dumps(summary["operation"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "run", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    score(parser.parse_args())
