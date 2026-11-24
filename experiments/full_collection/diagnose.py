"""Locate target losses and estimate grouped uncertainty from a completed replay."""

import argparse
import collections
import json
from pathlib import Path

from collection import digest, write


def first_loss(target, record):
    if target is None:
        return "target_name_absent"
    if record["status"] != "ok":
        return "request_error"
    stages = record["trace"]["stages"]
    if target in [d["id"] for d in record["results"][:10]]:
        return "retrieved_top10"
    if target not in set(stages.get("bm25", [])) | set(stages.get("semantic", [])):
        return "not_in_retrieval_union"
    for stage in ("fusion", "selection", "package_filter", "reranker_input"):
        if target not in stages.get(stage, []):
            return "lost_at_" + stage
    if target not in [d["id"] for d in record["results"]]:
        return "removed_by_output_filter"
    return "reranked_below_top10"


def grouped_intervals(rows, draws=2000):
    import numpy as np

    outputs = []
    sources = sorted(
        {
            row["source"]
            for row in rows
            if row["label_kind"]
            in {
                "upstream_single_gold",
                "upstream_alternative_premises",
                "reply_link_proxy",
            }
        }
    )
    for source in sources:
        groups = collections.defaultdict(list)
        for row in rows:
            if row["source"] == source and row["metrics"]:
                groups[row["group"]].append(row)
        if not groups:
            continue
        blocks = list(groups.values())
        n = np.array([len(g) for g in blocks], dtype=float)
        rng = np.random.default_rng(42)
        samples = rng.integers(0, len(blocks), size=(draws, len(blocks)))
        denominators = n[samples].sum(axis=1)
        for baseline in (
            "pre_rerank_same_pool",
            "neural_only",
            "without_final_dependency",
        ):
            for metric in ("success@1", "ndcg@10"):
                differences = np.array(
                    [
                        sum(
                            r["metrics"]["current_mixture"][metric]
                            - r["metrics"][baseline][metric]
                            for r in g
                        )
                        for g in blocks
                    ]
                )
                estimates = differences[samples].sum(axis=1) / denominators
                outputs.append(
                    dict(
                        source=source,
                        baseline=baseline,
                        metric=metric,
                        groups=len(blocks),
                        requests=int(n.sum()),
                        delta=float(differences.sum() / n.sum()),
                        interval95=np.quantile(estimates, [0.025, 0.975]).tolist(),
                        draws=draws,
                    )
                )
    return outputs


def diagnose(args):
    cases = json.loads(args.cases.read_text())["cases"]
    availability = json.loads((args.run / "target-availability.json").read_text())
    completion = json.loads((args.run / "complete.json").read_text())
    if digest(args.run / "records.jsonl") != completion["records_sha256"]:
        raise ValueError("Run integrity mismatch")
    loss = collections.defaultdict(collections.Counter)
    for case, line in zip(cases, (args.run / "records.jsonl").open(), strict=True):
        record = json.loads(line)
        if record["query_id"] != case["id"]:
            raise ValueError("Schedule mismatch")
        for membership in case["memberships"]:
            for target in membership["targets"]:
                loss[membership["source"]][
                    first_loss(availability.get(target), record)
                ] += 1
    rows = [json.loads(line) for line in (args.scores / "per-query.jsonl").open()]
    write(
        args.out,
        dict(
            target_record_losses={k: dict(v) for k, v in loss.items()},
            grouped_paired_intervals=grouped_intervals(rows),
            uncertainty="Exploratory paired percentile bootstrap, seed 42, grouped by upstream target/problem or source topic. Conditional on recorded labels; no annotation-error uncertainty or multiplicity-adjusted claim.",
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cases", "run", "scores", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    diagnose(parser.parse_args())
