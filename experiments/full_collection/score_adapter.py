"""Score all fixed-pool adapter conditions against their unchanged baseline."""

import argparse
import collections
import json
from pathlib import Path

from collection import digest, write
from score import metrics, rankings


def score(args):
    cases = {c["id"]: c for c in json.loads(args.cases.read_text())["cases"]}
    contract = json.loads((args.ablation / "contract.json").read_text())
    completion = json.loads((args.ablation / "complete.json").read_text())
    if (
        digest(args.cases) != contract["cases_sha256"]
        or digest(args.ablation / "records.jsonl") != completion["records_sha256"]
    ):
        raise ValueError("Changed adapter inputs")
    if digest(args.base / "contract.json") != contract["base_contract_sha256"]:
        raise ValueError("Baseline contract changed")
    expected = contract["scheduled_ids"]
    ids = set(expected)
    base = {}
    with (args.base / "records.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row["query_id"] in ids:
                base[row["query_id"]] = row
            if set(base) == ids:
                break
    if set(base) != ids:
        raise ValueError("Missing baseline records")
    availability = json.loads((args.base / "target-availability.json").read_text())
    totals = collections.defaultdict(
        lambda: dict(
            n=0, sums=collections.defaultdict(lambda: collections.defaultdict(float))
        )
    )
    per_query = []
    with (args.ablation / "records.jsonl").open() as stream:
        for identifier, line in zip(expected, stream, strict=True):
            row = json.loads(line)
            if row["query_id"] != identifier:
                raise ValueError("Adapter schedule mismatch")
            original = base[identifier]
            if row["candidate_ids"] != (original.get("fixed_pool") or {}).get(
                "candidate_ids", []
            ):
                raise ValueError("Candidate pool changed")
            methods = {
                k: rankings(original)[k]
                for k in ("current_mixture", "neural_only", "pre_rerank_same_pool")
            }
            for condition in contract["conditions"]:
                for mode in ("neural", "mixture"):
                    methods[condition + "_" + mode] = (
                        row["conditions"].get(condition, {}).get(mode, [])
                    )
            case = cases[identifier]
            for member in case["memberships"]:
                if not member["targets"]:
                    continue
                targets = {
                    availability[t]
                    if availability.get(t) is not None
                    else "absent:" + t
                    for t in member["targets"]
                }
                routes = [
                    [
                        availability[t]
                        if availability.get(t) is not None
                        else "absent:" + t
                        for t in route
                    ]
                    for route in member.get("routes", [])
                ]
                values = {
                    method: metrics(ranking, targets, routes)
                    for method, ranking in methods.items()
                }
                for axis, category in [
                    ("all", "all"),
                    ("form", case["categories"]["form"]),
                    ("upstream_style", member.get("upstream_style", "unspecified")),
                ]:
                    total = totals[
                        member["source"], member["label_kind"], axis, category
                    ]
                    total["n"] += 1
                    for method, items in values.items():
                        for metric, value in items.items():
                            total["sums"][method][metric] += value
                per_query.append(
                    dict(
                        query_id=identifier,
                        source=member["source"],
                        group=member.get("group", member["source_id"]),
                        metrics=values,
                    )
                )
    summaries = [
        dict(
            source=s,
            label_kind=k,
            axis=a,
            category=c,
            requests=t["n"],
            metrics={
                method: {metric: value / t["n"] for metric, value in items.items()}
                for method, items in t["sums"].items()
            },
        )
        for (s, k, a, c), t in sorted(totals.items())
    ]
    # Paired intervals for adapter changes, preserving target/topic groups.
    import numpy as np

    intervals = []
    sources = sorted(
        {
            row["source"]
            for row in summaries
            if row["label_kind"]
            in {
                "upstream_single_gold",
                "upstream_alternative_premises",
                "reply_link_proxy",
            }
        }
    )
    for source in sources:
        grouped = collections.defaultdict(list)
        for row in per_query:
            if row["source"] == source:
                grouped[row["group"]].append(row)
        blocks = list(grouped.values())
        if not blocks:
            continue
        n = np.array([len(block) for block in blocks])
        samples = np.random.default_rng(42).integers(
            0, len(blocks), size=(2000, len(blocks))
        )
        for method in (
            "chat_yes_no_256_mixture",
            "chat_yes_no_512_mixture",
            "chat_yes_no_256_neural",
            "chat_yes_no_512_neural",
        ):
            for metric in ("success@1", "ndcg@10"):
                sums = np.array(
                    [
                        sum(
                            row["metrics"][method][metric]
                            - row["metrics"]["current_mixture"][metric]
                            for row in block
                        )
                        for block in blocks
                    ]
                )
                draws = sums[samples].sum(axis=1) / n[samples].sum(axis=1)
                intervals.append(
                    dict(
                        source=source,
                        method=method,
                        metric=metric,
                        groups=len(blocks),
                        delta=float(sums.sum() / n.sum()),
                        interval95=np.quantile(draws, [0.025, 0.975]).tolist(),
                    )
                )
    write(
        args.out,
        dict(
            scheduled=len(expected),
            selection=contract["selection"],
            slices=summaries,
            paired_intervals=intervals,
            scope="Exploratory fixed-pool comparison on every request with recorded targets. Custom yes/no system instruction with model-card-compatible chat wrapping. No new training or deployment.",
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "base", "ablation", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    score(parser.parse_args())
