"""Audit complete baseline/corrected journals and compare paired labelled scores."""

import argparse
import collections
import json
import math
from pathlib import Path

import numpy as np

from collection import digest, write


def verified_journal(directory):
    completion = json.loads((directory / "complete.json").read_text())
    if digest(directory / "records.jsonl") != completion["records_sha256"]:
        raise ValueError("Changed journal")
    if digest(directory / "contract.json") != completion["contract_sha256"]:
        raise ValueError("Changed contract")
    return directory / "records.jsonl"


def compare(args):
    baseline_path = verified_journal(args.base)
    corrected_path = verified_journal(args.corrected)
    cases = json.loads(args.cases.read_text())["cases"]
    changed = collections.Counter()
    source_changes = collections.defaultdict(collections.Counter)
    with baseline_path.open() as baseline, corrected_path.open() as corrected:
        for case, first, second in zip(cases, baseline, corrected, strict=True):
            first, second = json.loads(first), json.loads(second)
            if first["query_id"] != case["id"] or second["query_id"] != case["id"]:
                raise ValueError("Mismatched requests")
            if first["status"] != second["status"]:
                raise ValueError("Changed request status")
            first_pool = (first.get("fixed_pool") or {}).get("candidate_ids", [])
            second_pool = (second.get("fixed_pool") or {}).get("candidate_ids", [])
            if first_pool != second_pool:
                raise ValueError("Candidate pool changed")
            if len(first_pool) != len(set(first_pool)):
                raise ValueError("Duplicate pool candidates")
            for row in (first, second):
                for values in (row.get("fixed_pool") or {}).get("scores", {}).values():
                    if len(values) != len(first_pool) or not all(
                        math.isfinite(v) for v in values
                    ):
                        raise ValueError("Invalid score vector")
                result_ids = [d["id"] for d in row["results"]]
                if len(result_ids) != len(set(result_ids)) or len(result_ids) > 25:
                    raise ValueError("Invalid returned result IDs")
                traced_results = row["trace"]["stages"].get("results")
                if traced_results is not None and traced_results != result_ids:
                    raise ValueError("Result trace disagrees with the returned ranking")
                if case["packages"] and any(
                    d["module"].split(".")[0] not in case["packages"]
                    for d in row["results"]
                ):
                    raise ValueError("Package filter violated")
            for stage in ("bm25", "semantic", "fusion", "selection"):
                if first["trace"]["stages"].get(stage) != second["trace"]["stages"].get(
                    stage
                ):
                    raise ValueError("Retrieval changed")
            before = [d["id"] for d in first["results"]]
            after = [d["id"] for d in second["results"]]
            if set(before) != set(after):
                raise ValueError("Output set changed")
            changes = dict(
                requests=1,
                top1_changed=int(before[:1] != after[:1]),
                order_changed=int(before != after),
            )
            changed.update(changes)
            for member in case["memberships"]:
                source_changes[member["source"]].update(changes)
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    with (
        (args.base_scores / "per-query.jsonl").open() as base,
        (args.corrected_scores / "per-query.jsonl").open() as corrected,
    ):
        for first, second in zip(base, corrected, strict=True):
            first, second = json.loads(first), json.loads(second)
            for field in (
                "query_id",
                "source",
                "source_id",
                "group",
                "label_kind",
                "target_count",
            ):
                if first[field] != second[field]:
                    raise ValueError("Score membership changed")
            if first["metrics"]:
                groups[first["source"]][first["group"]].append(
                    {
                        metric: second["metrics"]["current_mixture"][metric] - value
                        for metric, value in first["metrics"]["current_mixture"].items()
                    }
                )
    intervals = []
    for source, grouped in sorted(groups.items()):
        blocks = list(grouped.values())
        counts = np.array([len(block) for block in blocks])
        samples = np.random.default_rng(42).integers(
            0, len(blocks), size=(2000, len(blocks))
        )
        for metric in ("success@1", "success@10", "ndcg@10", "recall@10"):
            sums = np.array([sum(row[metric] for row in block) for block in blocks])
            draws = sums[samples].sum(axis=1) / counts[samples].sum(axis=1)
            intervals.append(
                dict(
                    source=source,
                    metric=metric,
                    groups=len(blocks),
                    delta=float(sums.sum() / counts.sum()),
                    interval95=np.quantile(draws, [0.025, 0.975]).tolist(),
                )
            )
    write(
        args.out,
        dict(
            operation=dict(changed),
            sources=dict(source_changes),
            paired_intervals=intervals,
            scope="Corrected 256-token production client versus baseline, identical candidate pools and visible output sets; exploratory grouped intervals.",
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "cases",
        "base",
        "corrected",
        "base-scores",
        "corrected-scores",
        "out",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    compare(parser.parse_args())
