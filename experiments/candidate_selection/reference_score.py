"""Score frozen MathlibQR target recovery without inference dependencies."""

import argparse
import collections
import json
import math
import random
from pathlib import Path

CONFIGS = {
    "lexical": "bm25",
    "dense": "semantic",
    "fusion": "fusion",
    "selection": "selection",
}
METRICS = {
    "nDCG@1": (1, True),
    "nDCG@5": (5, True),
    "nDCG@10": (10, True),
    "Recall@10": (10, False),
    "Recall@50": (50, False),
    "Recall@100": (100, False),
}


def value(rank, cutoff, discounted):
    if rank is None or rank > cutoff:
        return 0.0
    return 1.0 / math.log2(rank + 1) if discounted else 1.0


def position(items, target):
    return items.index(target) + 1 if target in items else None


def summarize(rows, bootstrap=2000):
    if not rows:
        raise ValueError("Empty scoring slice")
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row["group"]].append(row)
    result = {
        "queries": len(rows),
        "bootstrap_draws": bootstrap,
        "target_groups": len(groups),
        "request_errors": sum(r["status"] != "ok" for r in rows),
        "configurations": {},
    }
    group_rows = list(groups.values())
    rng = random.Random(42)
    samples = [
        [rng.randrange(len(group_rows)) for _ in group_rows] for _ in range(bootstrap)
    ]
    counts = [len(g) for g in group_rows]
    denominators = [sum(counts[i] for i in sample) for sample in samples]
    for config in rows[0]["ranks"]:
        metrics = {}
        for metric, (cutoff, discounted) in METRICS.items():
            sums = [
                sum(value(r["ranks"][config], cutoff, discounted) for r in group)
                for group in group_rows
            ]
            draws = sorted(
                sum(sums[i] for i in sample) / n
                for sample, n in zip(samples, denominators)
            )
            metrics[metric] = {
                "query_micro": sum(sums) / len(rows),
                "target_macro": sum(s / n for s, n in zip(sums, counts)) / len(groups),
                "cluster_bootstrap_95": [
                    draws[int(0.025 * (bootstrap - 1))],
                    draws[int(0.975 * (bootstrap - 1))],
                ],
            }
        result["configurations"][config] = metrics
    return result


def score(cases, replay, shared, upstream):
    expected = [c["id"] for c in cases["cases"]]
    if replay["state"] != "complete" or replay["scheduled_ids"] != expected:
        raise ValueError("Require completed frozen schedule")
    records = {r["query_id"]: r for r in replay["records"]}
    if len(records) != len(replay["records"]) or set(records) != set(expected):
        raise ValueError("Duplicate or missing request records")
    originals = {entry["id"]: entry for entry in upstream}
    rows = []
    for case in cases["cases"]:
        (target,) = case["targets"]
        record = records[case["id"]]
        available = replay["target_availability"][target]
        target_id = None if available is None else available["id"]
        ranks = {}
        for config, stage in CONFIGS.items():
            ids = record.get("trace", {}).get("stages", {}).get(stage, [])[:100]
            ranks[config] = (
                position(ids, target_id) if record["status"] == "ok" else None
            )
        visible = (
            [d["name"] for d in record["results"]] if record["status"] == "ok" else []
        )
        ranks["current_mixture_100"] = position(visible, target)
        pool = record.get("fixed_pool") or {}
        for config in ("neural_only", "without_final_dependency"):
            names = [
                name
                for name in pool.get("rankings", {}).get(config, [])
                if name in visible
            ]
            ranks[config + "_100"] = (
                position(names, target) if record["status"] == "ok" else None
            )
        names = [name for name in pool.get("pre_rerank_names", []) if name in visible]
        ranks["pre_rerank_same_pool_100"] = (
            position(names, target) if record["status"] == "ok" else None
        )
        group = case["provenance"]["source_record"]
        original = originals[group]
        rows.append(
            {
                "id": case["id"],
                "group": group,
                "target": target,
                "present": available is not None,
                "shared171": target in shared["shared_declarations"],
                "style": case["provenance"]["source_field"],
                "difficulty": original["difficulty"],
                "kind": original["kind"],
                "status": record["status"],
                "ranks": ranks,
            }
        )
    slices = {
        "full": rows,
        "shared171": [r for r in rows if r["shared171"]],
        "present_only": [r for r in rows if r["present"]],
    }
    summary = {
        "condition": "mathlibqr-remapped-v1",
        "label_source": "upstream single gold; no local AI relevance judgment",
        "corpus_revision": replay["corpus_revision"],
        "settings": replay["settings"],
        "uncertainty": (
            "2000 seeded percentile bootstrap draws resampling upstream target "
            "groups; micro estimate recomputed per draw. Descriptive sampling "
            "uncertainty, not model or annotation uncertainty."
        ),
        "absent_targets": sorted({r["target"] for r in rows if not r["present"]}),
        "slices": {name: summarize(items) for name, items in slices.items()},
    }
    summary["style_slices"] = {
        style: summarize([r for r in rows if r["style"] == style], bootstrap=500)
        for style in sorted({r["style"] for r in rows})
    }
    summary["top1_changed"] = sum(
        r.get("fixed_pool") is not None
        and [
            name
            for name in r["fixed_pool"]["pre_rerank_names"]
            if name in {d["name"] for d in r["results"]}
        ][:1]
        != [d["name"] for d in r["results"][:1]]
        for r in replay["records"]
    )
    return rows, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--run-directory", default="reference-run")
    args = parser.parse_args()

    def read(name):
        return json.loads((args.root / name).read_text(encoding="utf-8"))

    rows, summary = score(
        read("mathlibqr-cases.frozen.json"),
        read(args.run_directory + "/replay.json"),
        read("upstream/benchmark/MathlibQR_shared171.json"),
        read("upstream/benchmark/MathlibQR.json"),
    )
    (args.root / "reference-per-query.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.root / "reference-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print({name: data["queries"] for name, data in summary["slices"].items()})
