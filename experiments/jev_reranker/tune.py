"""Retune LeanExplore's final-score weights for a reranker, with cross-validation.

The final score is  reranker + bm25 * BM25 + dependency * dependents + fuzzy * name match
(the name term only when the raw match reaches a threshold). The grid also tries the
raw reranker probability in place of its min-max normalized value. Weights are chosen
on four folds by mean nDCG@10 and scored on the fifth, so the cross-validated figure
is not flattered by the tuning. Folds are stratified by query type.
"""

import argparse
import itertools
import json
from pathlib import Path

from compare import mean, metrics, normalize, ranking, table

GRID = {
    "bm25": (0.0, 0.05, 0.1, 0.2, 0.4),
    "dependency": (0.0, 0.05, 0.1, 0.2),
    "fuzzy": (0.0, 0.25, 0.5, 1.0),
    "threshold": (0.7, 0.9),
    "normalize": (True, False),
}
DEPLOYED = {"bm25": 0.4, "dependency": 0.2, "fuzzy": 1.0, "threshold": 0.7,
            "normalize": True}
FOLDS = 5


def load(path: str) -> dict[str, dict]:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    return {row["id"]: row for row in rows}


def final(scores: list[float], signals: dict, w: dict) -> list[float]:
    neural = normalize(scores) if w["normalize"] else scores
    return [
        n + w["bm25"] * b + w["dependency"] * d
        + (w["fuzzy"] * fn if f >= w["threshold"] else 0.0)
        for n, b, d, f, fn in zip(neural, signals["bm25"], signals["dependency"],
                                  signals["fuzzy"], signals["fuzzy_normalized"])
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pools", required=True)
    parser.add_argument("--components", required=True)
    parser.add_argument("--scores", nargs="+", required=True, metavar="LABEL=PATH")
    args = parser.parse_args()

    pools, components = load(args.pools), load(args.components)
    ids = list(pools)
    fold = {}
    by_type: dict[str, list[str]] = {}
    for query_id in ids:
        by_type.setdefault(pools[query_id]["query_type"], []).append(query_id)
    for members in by_type.values():
        for position, query_id in enumerate(members):
            fold[query_id] = position % FOLDS
    configs = [dict(zip(GRID, values)) for values in itertools.product(*GRID.values())]

    rows, by_query_type = [], []
    for item in args.scores:
        label, path = item.split("=", 1)
        scores = {i: row["scores"] for i, row in load(path).items()}

        def ndcg(query_id: str, w: dict | None) -> float:
            pool = pools[query_id]["candidates"]
            values = scores[query_id]
            if w is not None:
                values = final(values, components[query_id], w)
            return metrics(ranking(pool, values), pools[query_id]["judgments"])["ndcg@10"]

        grid = [{i: ndcg(i, w) for i in ids} for w in configs]
        held_out = {}
        for k in range(FOLDS):
            train = [i for i in ids if fold[i] != k]
            best = max(grid, key=lambda per: mean([per[i] for i in train]))
            held_out.update({i: best[i] for i in ids if fold[i] == k})
        winner = max(range(len(configs)), key=lambda c: mean(list(grid[c].values())))
        chosen = configs[winner]
        rows.append([
            label,
            f"{mean([ndcg(i, None) for i in ids]):.3f}",
            f"{mean([ndcg(i, DEPLOYED) for i in ids]):.3f}",
            f"{mean(list(held_out.values())):.3f}",
            f"{mean(list(grid[winner].values())):.3f}",
            ", ".join(f"{k}={v}" for k, v in chosen.items()),
        ])
        types = sorted(by_type)
        by_query_type.append([label, *(
            f"{mean([held_out[i] for i in by_type[t]]):.3f}" for t in types
        )])

    print("nDCG@10 over", len(ids), "queries\n")
    print(table(["Reranker", "score alone", "deployed weights", "retuned (cross-validated)",
                 "retuned (fit on all)", "weights fit on all"], rows))
    print("\nRetuned (cross-validated) nDCG@10 by query type\n")
    print(table(["Reranker", *sorted(by_type)], by_query_type))


if __name__ == "__main__":
    main()
