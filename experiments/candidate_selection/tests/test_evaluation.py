"""Checks for paired experiments, relevance metrics and corpus validation."""

import json
import math

import pytest

from runner import (
    load_queries,
    ranking_metrics,
    resolve_targets,
    run_experiment,
    summarize,
    variants,
)


def test_metrics_count_multiple_acceptable_lemmas():
    """Known labels at ranks two and three yield hand-computed ranking metrics."""
    measured = ranking_metrics([9, 2, 3], {2, 3, 4}, 3)
    assert measured["recall"] == 2 / 3
    assert measured["mrr"] == 1 / 2
    assert measured["hit"] == 1
    assert measured["ndcg"] == pytest.approx(
        (1 / math.log2(3) + 1 / math.log2(4))
        / (1 + 1 / math.log2(3) + 1 / math.log2(4))
    )
    assert ranking_metrics([], {2}, 5) == dict(hit=0, recall=0, mrr=0, ndcg=0)


async def test_missing_target_stops_before_model_calls(engine):
    """An incompatible corpus is rejected rather than counted as a retrieval miss."""
    with pytest.raises(ValueError, match="absent from corpus"):
        await resolve_targets(engine, [{"id": "missing", "relevant": ["NotInCorpus"]}])
    assert engine._embedding_client.calls == []


async def test_grid_is_paired_and_does_not_export_query_text(engine):
    """Every query sees all 12 variants, with stage recall and separate latency."""
    queries = [
        {
            "id": "a",
            "query": "commutative",
            "category": "short",
            "relevant": ["Nat.add_comm"],
        },
        {"id": "b", "query": "List.map", "category": "name", "relevant": ["List.map"]},
    ]
    records = await run_experiment(engine, queries, limit=5, retrieval_depth=20)
    assert len(records) == 24
    for query in queries:
        rows = [row for row in records if row["query_id"] == query["id"]]
        assert len(rows) == len(variants(5)) == 12
        assert len({json.dumps(row["variant"], sort_keys=True) for row in rows}) == 12
        assert all("query" not in row and row["latency_ms"] >= 0 for row in rows)
        assert all(
            row["stages"]["reranker_input"]["count"] <= row["variant"]["depth"]
            for row in rows
        )
    summary = summarize(records)
    overall = [row for row in summary if row["category"] == "__all__"]
    assert len(overall) == 12
    assert all(row["queries"] == 2 for row in overall)


@pytest.mark.parametrize(
    "changes",
    [
        {"relevant": []},
        {"query": " "},
        {"relevant": ["Nat.add", "Nat.add"]},
        {"packages": "Mathlib"},
    ],
)
def test_invalid_labels_and_queries_are_rejected(tmp_path, changes):
    """Malformed query records cannot silently distort denominators or filters."""
    query = {
        "id": "x",
        "query": "addition",
        "category": "short",
        "relevant": ["Nat.add"],
    }
    query.update(changes)
    path = tmp_path / "queries.json"
    path.write_text(json.dumps([query]))
    with pytest.raises(ValueError):
        load_queries(path)
