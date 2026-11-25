from typing import Any

import pytest

from lean_explore_bench import score
from lean_explore_bench.record import QueryRecord


def _record(i: int, query_type: str, library: str, split: str) -> QueryRecord:
    return QueryRecord(
        id=f"q{i}",
        query=f"query {i}",
        query_type=query_type,
        variant="v",
        source="declaration",
        library=library,
        area="Algebra",
        target=f"T{i}",
        judgments={f"T{i}": 3},
        group_id=f"T{i}",
        track="human",
        split=split,
    )


RECORDS = [
    _record(0, "informal", "mathlib", "test"),
    _record(1, "informal", "cslib", "test"),
    _record(2, "name", "mathlib", "development"),
    _record(3, "name", "cslib", "test"),
]
RESULTS: dict[str, dict[str, Any]] = {
    "q0": {"status": "ok", "documents": ["T0", "X"], "latency_ms": 5.0},
    "q1": {"status": "ok", "documents": ["X", "T1"]},
    "q2": {"status": "ok", "documents": ["X", "Y"]},
    # q3 has no result: a failed request.
}


def test_scores_are_grouped_by_query_type_and_library() -> None:
    report = score.score(RECORDS, RESULTS, "demo", limit=2)
    assert report["engine"] == "demo" and report["split"] == "all"
    assert report["corpus_revision"] == score.HOSTED_REVISION
    assert report["overall"]["queries"] == 4
    assert report["overall"]["request_success"] == pytest.approx(0.75)
    assert report["overall"]["success@1"] == pytest.approx(0.25)
    informal = report["by_query_type"]["informal"]
    assert informal["queries"] == 2
    assert informal["success@1"] == pytest.approx(0.5)
    assert informal["success@2"] == pytest.approx(1.0)
    assert informal["mrr@2"] == pytest.approx(0.75)
    assert report["by_query_type"]["name"]["success@2"] == 0.0
    assert report["by_library"]["mathlib"]["success@2"] == pytest.approx(0.5)
    assert list(report["by_library"]) == ["cslib", "mathlib"]


def test_split_filter_and_rendering() -> None:
    report = score.score(RECORDS, RESULTS, "demo", split="test", limit=2)
    assert report["overall"]["queries"] == 3
    assert set(report["by_query_type"]) == {"informal", "name"}
    text = score.render(report)
    assert text.startswith("### demo (test queries)")
    assert "| Query type | Queries | success@1 | success@2 | mrr@2 | ndcg@2 |" in text
    assert "| informal | 2 | 0.500 | 1.000 | 0.750 |" in text
    assert "| **All** | 3 |" in text
    assert "| Library | Queries |" in text
    assert "| success@2 by query type and library | cslib | mathlib |" in text
    cells = report["by_type_and_library"]
    assert all(" / " in key for key in cells)
    assert sum(values["queries"] for values in cells.values()) == 3
    row = [line for line in text.splitlines() if line.startswith("| name |")][-1]
    assert row.count("(") == len({key for key in cells if key.startswith("name / ")})


def test_benchmark_score_is_the_mean_of_the_buckets() -> None:
    thread = QueryRecord.from_json(
        {**_record(4, "question", "mathlib", "test").to_json(), "source": "zulip"}
    )
    results = {**RESULTS, "q4": {"status": "ok", "documents": ["T4"]}}
    report = score.score([*RECORDS, thread], results, "demo", limit=2)
    buckets = report["by_bucket"]
    assert set(buckets) == {"informal", "names and keywords", "real questions"}
    assert buckets["real questions"]["success@1"] == 1.0
    assert buckets["names and keywords"]["queries"] == 2
    expected = (0.5 + 0.0 + 1.0) / 3
    assert report["benchmark"]["success@1"] == pytest.approx(expected)
    text = score.render(report)
    assert "| Bucket | Queries |" in text
    assert f"Benchmark score (mean of the buckets): success@1 {expected:.3f}" in text
