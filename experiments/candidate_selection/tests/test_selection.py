"""Candidate selection regressions using real indices and controlled rankings."""

from unittest.mock import patch

import pytest

from lean_explore.search.trace import SearchTrace


async def test_zero_bm25_matches_do_not_enter_fusion(engine):
    """An unknown lexical query leaves only semantic candidates in fusion."""
    trace = SearchTrace()
    await names(engine, "zzzzunknownword", exclude_zero_bm25=True, trace=trace)
    assert trace.stages["bm25_raw"]
    assert trace.stages["bm25"] == []
    assert set(trace.stages["fusion"]) == set(trace.stages["semantic"])


async def test_positive_bm25_matches_survive(engine):
    """Removing zero scores still admits a declaration found by its name."""
    trace = SearchTrace()
    await names(engine, "Nat.add", exclude_zero_bm25=True, trace=trace)
    assert 1 in trace.stages["bm25"]
    assert set(trace.stages["bm25"]) <= set(trace.stages["bm25_raw"])


@pytest.mark.parametrize("depth,expected", [(1, "Nat.add"), (3, "Nat.add_comm")])
async def test_deeper_reranking_can_recover_a_discarded_lemma(engine, depth, expected):
    """A relevant lemma below the output limit can reach the final top result."""
    trace = SearchTrace()
    with (
        patch.object(
            engine.indexes, "name_candidates", return_value={1: 9, 5: 8, 2: 7}
        ),
        patch.object(engine, "_semantic_candidates", return_value={}),
    ):
        results = await names(
            engine,
            "commutative",
            limit=1,
            rerank_top=depth,
            dependency_boost=False,
            trace=trace,
        )
    assert results == [expected]
    assert trace.stages["selection"] == [1, 5, 2]
    assert len(trace.stages["reranker_input"]) == depth
    assert len(trace.stages["results"]) == 1


async def test_boost_toggle_changes_only_selection(engine):
    """The ablation preserves retrieval/fusion and the top-500 pool boundary."""
    traces = [SearchTrace(), SearchTrace()]
    for enabled, trace in zip((True, False), traces):
        await names(
            engine, "addition commutative", dependency_boost=enabled, trace=trace
        )
    assert traces[0].stages["fusion"] == traces[1].stages["fusion"]
    assert traces[1].stages["selection"] == traces[1].stages["fusion"][:500]
    assert traces[0].stages["selection"] != traces[1].stages["selection"]


async def test_trace_resets_and_does_not_change_results(engine):
    """Tracing preserves rankings, reports ordered times and clears stale data."""
    trace = SearchTrace()
    baseline = await names(engine, "Nat.add")
    assert await names(engine, "Nat.add", trace=trace) == baseline
    times = list(trace.elapsed_ms.values())
    assert times == sorted(times)
    assert times[0] >= 0
    await names(engine, " ", trace=trace)
    assert trace.stages == trace.elapsed_ms == {}


async def test_empty_filtered_pool_skips_reranker(engine):
    """Package filtering can empty the pool without calling the model."""
    trace = SearchTrace()
    assert await names(engine, "Nat.add", packages=["Missing"], trace=trace) == []
    assert trace.stages["reranker_input"] == trace.stages["results"] == []
    assert engine._reranker_client.calls == []


async def names(engine, query: str, **options) -> list[str]:
    """Search the synthetic corpus with a valid retrieval depth."""
    results = await engine.search(query, **{"bm25_k": 20, **options})
    return [result.name for result in results]
