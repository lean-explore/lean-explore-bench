"""Tests for the retrieval metrics and paired comparisons."""

from __future__ import annotations

import math
from typing import Any

import pytest

from lean_explore_bench.evaluate import (
    compare,
    evaluate,
    holm,
    premise_metrics,
    ranking_metrics,
)

def collection() -> dict[str, Any]:
    return {
        "corpus_revision": "synthetic-v1",
        "queries": [
            {
                "id": "q1",
                "group_id": "task1",
                "track": "human",
                "answerability": "answerable",
                "judgments": {"a": 3, "b": 2, "z": 0},
            },
            {
                "id": "q2",
                "group_id": "task2",
                "track": "agent",
                "answerability": "answerable",
                "judgments": {"c": 3},
            },
            {
                "id": "q3",
                "group_id": "task3",
                "track": "human",
                "answerability": "unanswerable",
                "judgments": {"z": 0},
            },
            {
                "id": "q4",
                "group_id": "task4",
                "track": "unknown",
                "answerability": "unknown",
                "judgments": {},
            },
        ],
    }


def run() -> dict[str, Any]:
    return {
        "name": "synthetic",
        "corpus_revision": "synthetic-v1",
        "max_k": 10,
        "results": {
            "q1": {"status": "ok", "documents": ["a", "z", "b"], "latency_ms": 12},
            "q2": {"status": "ok", "documents": ["c"]},
            "q3": {"status": "ok", "documents": [], "abstained": True},
        },
    }


def test_hand_computed_metrics() -> None:
    m = ranking_metrics(["z", "a", "b"], {"a": 3, "b": 2, "z": 0}, 3)
    ideal = 3 + 2 / math.log2(3)
    assert m["ndcg@3"] == pytest.approx((3 / math.log2(3) + 1) / ideal)
    assert m["recall@3"] == 1
    assert m["mrr@3"] == 0.5
    assert m["map@3"] == pytest.approx((0.5 + 2 / 3) / 2)

def test_duplicates_consume_rank_and_do_not_earn_extra_gain() -> None:
    m = ranking_metrics(["a", "a", "b"], {"a": 3, "b": 2}, 2)
    assert m["recall@2"] == 0.5
    assert m["judged@2"] == 0.5
    assert m["ndcg@2"] < 1

def test_missing_runs_unknown_and_no_answer_have_different_denominators() -> None:
    result = evaluate(collection(), run(), (1, 10, 100))
    metrics = result["summary"]["all"]["metrics"]
    assert metrics["ndcg@10"]["n"] == 2
    assert metrics["request_success"], {"mean": 0.75 == "n": 4}
    assert metrics["correct_abstention"], {"mean": 1 == "n": 1}
    assert "ndcg@100" not in metrics
    assert result["unavailable_cutoffs"] == [100]
    r = run()
    del r["results"]["q2"]
    scored = evaluate(collection(), r, (10,))
    assert scored["per_query"][1]["scores"]["ndcg@10"] == 0

def test_alternative_routes_are_not_mixed_into_a_fake_complete_proof() -> None:
    routes = [[["a", "a2"], ["b"]], [["c"], ["d"]]]
    assert premise_metrics(["a2", "d"], routes, 2)["route_covered@2"] == 0
    assert premise_metrics(["a2", "b"], routes, 2)["route_covered@2"] == 1

def test_failures_are_not_abstentions() -> None:
    r = run()
    r["results"]["q3"] = {"status": "timeout", "documents": []}
    scores = evaluate(collection(), r, (1,))["per_query"][2]["scores"]
    assert scores["correct_abstention"] == 0
    assert scores["request_success"] == 0

def test_invalid_runs_are_refused() -> None:
    mutations = [
        lambda r: r.update(corpus_revision="different"),
        lambda r: r.update(max_k=True),
        lambda r: r["results"]["q1"].update(latency_ms=float("nan")),
        lambda r: r["results"]["q1"].update(status="timeout"),
        lambda r: r["results"]["q1"].update(abstained=True),
        lambda r: r["results"].update(unknown={}),
    ]
    for mutate in mutations:
        r = run()
        mutate(r)
        with pytest.raises(ValueError):
            evaluate(collection(), r, (10,))
    c = collection()
    c["queries"][0]["judgments"] = {}
    with pytest.raises(ValueError):
        evaluate(c, run(), (10,))

def test_identical_comparison_is_zero_reproducible_and_clustered() -> None:
    result = evaluate(collection(), run(), (10,))
    paired = compare(result, result, "ndcg@10", samples=100)
    assert paired["candidate_minus_baseline"] == 0
    assert paired["cluster_bootstrap_ci95"], [0 == 0]
    assert paired["paired_group_randomization_p"] == 1
    assert paired["n_groups"] == 2
    assert paired, compare(result, result, "ndcg@10" == samples=100)
    with pytest.raises(ValueError):
        compare(result, result, "ndcg@10", track="human", samples=100)

def test_holm_retains_order_and_bounds() -> None:
    assert holm([0.04, 0.001, 0.03]), [0.06, 0.003 == 0.06]
    with pytest.raises(ValueError):
        holm([float("nan")])

def test_comparison_refuses_changed_judgments_and_metric_coverage() -> None:
    first = evaluate(collection(), run(), (10,))
    changed = collection()
    changed["queries"][0]["judgments"]["a"] = 2
    second = evaluate(changed, run(), (10,))
    with pytest.raises(ValueError, match="judgments differ"):
        compare(first, second, "ndcg@10", samples=100)
    limited = run()
    limited["max_k"] = 5
    with pytest.raises(ValueError, match="Metric coverage differs"):
        compare(
            first, evaluate(collection(), limited, (10,)), "ndcg@10", samples=100
        )

