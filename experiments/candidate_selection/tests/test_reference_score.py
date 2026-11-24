"""Single-gold scoring preserves failures, missing targets and group units."""

import copy

import pytest

from reference_score import score, summarize, value


def fixture():
    cases = {"cases": []}
    records = []
    upstream = []
    for i in range(3):
        name = f"Target{i}"
        cases["cases"].append(
            {
                "id": str(i),
                "targets": [name],
                "provenance": {"source_record": f"g{i}", "source_field": "q1c_natural"},
            }
        )
        records.append(
            {
                "query_id": str(i),
                "status": "ok" if i != 2 else "error",
                "results": [{"name": name}] if i == 0 else [],
                "trace": {
                    "stages": {
                        "bm25": [0],
                        "semantic": [0],
                        "fusion": [0],
                        "selection": [0],
                    }
                },
                "fixed_pool": {
                    "pre_rerank_names": [name],
                    "rankings": {
                        "neural_only": [name],
                        "without_final_dependency": [name],
                    },
                },
            }
        )
        upstream.append({"id": f"g{i}", "difficulty": "Easy", "kind": "theorem"})
    replay = {
        "state": "complete",
        "scheduled_ids": ["0", "1", "2"],
        "records": records,
        "target_availability": {
            "Target0": {"id": 0},
            "Target1": None,
            "Target2": {"id": 2},
        },
        "corpus_revision": "fixture",
        "settings": {},
    }
    shared = {"shared_declarations": ["Target0", "Target2"]}
    return cases, replay, shared, upstream


def test_absence_and_failure_stay_in_denominator():
    rows, result = score(*fixture())
    assert result["slices"]["full"]["queries"] == 3
    assert result["slices"]["present_only"]["queries"] == 2
    assert result["slices"]["full"]["request_errors"] == 1
    assert result["slices"]["full"]["configurations"]["current_mixture_100"][
        "Recall@100"
    ]["query_micro"] == pytest.approx(1 / 3)
    assert result["absent_targets"] == ["Target1"]
    assert all(rank is None for rank in rows[2]["ranks"].values())


def test_no_rank_padding_and_single_gold_discount():
    assert value(None, 100, True) == 0
    assert value(11, 10, True) == 0
    assert value(3, 5, True) == 0.5
    assert value(3, 5, False) == 1


def test_group_macro_differs_from_variant_micro():
    base = {"status": "ok", "group": "large", "ranks": {"example": 1}}
    rows = [copy.deepcopy(base) for _ in range(4)]
    rows.append({"status": "ok", "group": "small", "ranks": {"example": None}})
    result = summarize(rows, bootstrap=100)
    metric = result["configurations"]["example"]["Recall@10"]
    assert metric["query_micro"] == 0.8
    assert metric["target_macro"] == 0.5
    assert result == summarize(rows, bootstrap=100)


@pytest.mark.parametrize("fault", ["unfinished", "missing", "duplicate"])
def test_incomplete_schedules_rejected(fault):
    cases, replay, shared, upstream = fixture()
    if fault == "unfinished":
        replay["state"] = "running"
    elif fault == "missing":
        replay["records"].pop()
    else:
        replay["records"].append(replay["records"][0])
    with pytest.raises(ValueError):
        score(cases, replay, shared, upstream)
