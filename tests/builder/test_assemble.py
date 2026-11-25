from typing import Any

from lean_explore_bench.builder import assemble
from lean_explore_bench.builder.corpus import Corpus
from lean_explore_bench.builder.sample import Target, sample_targets
from lean_explore_bench.record import SPLITS, QueryRecord, to_collection
from lean_explore_bench.spec import MixSpec

SPEC = MixSpec(
    library_counts={"mathlib": 4, "cslib": 2},
    query_types=("prose", "goal"),
    reserve=0.5,
)


def _entry(target: Target, accepted: bool) -> dict[str, Any]:
    declaration = target.declaration
    record = QueryRecord(
        id=target.id,
        query=f"query for {declaration.name}",
        query_type=target.query_type,
        variant="statement",
        source="declaration",
        library=declaration.library,
        area=declaration.area,
        target=declaration.name,
        judgments={declaration.name: 3},
        group_id=declaration.name,
    )
    return {
        "id": target.id,
        "accepted": accepted,
        "record": record.to_json() if accepted else None,
    }


def test_needed_uses_reserves_only_to_replace_rejections(corpus: Corpus) -> None:
    targets = sample_targets(corpus, SPEC)
    cell = [
        target
        for target in targets
        if (target.query_type, target.declaration.library) == ("prose", "mathlib")
    ]
    assert len(cell) == 6
    first = assemble.needed(targets, {}, SPEC)
    assert len(first) == 2 * (4 + 2)
    assert all(target.order < 4 for target in first if target in cell)

    done = {target.id: _entry(target, target is not cell[1]) for target in first}
    second = assemble.needed(targets, done, SPEC)
    assert second == [cell[4]]
    done[cell[4].id] = _entry(cell[4], True)
    assert assemble.needed(targets, done, SPEC) == []

    chosen = assemble.select(targets, done, SPEC)
    assert len(chosen) == 12
    ids = {record.id for record in chosen}
    assert cell[1].id not in ids and cell[4].id in ids and cell[5].id not in ids


def test_select_caps_each_cell_at_its_quota(corpus: Corpus) -> None:
    targets = sample_targets(corpus, SPEC)
    done = {target.id: _entry(target, True) for target in targets}
    chosen = assemble.select(targets, done, SPEC)
    assert len(chosen) == 12
    assert assemble.select(targets, {}, SPEC) == []


def test_select_borrows_from_other_libraries_when_one_runs_out(corpus: Corpus) -> None:
    targets = sample_targets(corpus, SPEC)
    small = min(SPEC.library_counts, key=lambda name: SPEC.library_counts[name])
    done = {
        target.id: _entry(target, target.declaration.library != small)
        for target in targets
    }
    chosen = assemble.select(targets, done, SPEC)
    assert len(chosen) == 12
    assert all(record.library != small for record in chosen)


def test_journal_queries_outside_the_sample_count_when_allowed(corpus: Corpus) -> None:
    targets = sample_targets(corpus, SPEC)
    inside = [
        t
        for t in targets
        if (t.query_type, t.declaration.library) == ("prose", "mathlib")
    ]
    done = {target.id: _entry(target, True) for target in inside[:2]}
    extra = QueryRecord.from_json(
        {
            **done[inside[0].id]["record"],
            "id": "prose-mathlib-extra",
            "target": "Old.name",
        }
    )
    done[extra.id] = {"id": extra.id, "accepted": True, "record": extra.to_json()}
    pending = assemble.needed(targets, done, SPEC)
    assert (
        sum(
            t.query_type == "prose" and t.declaration.library == "mathlib"
            for t in pending
        )
        == 1
    )
    chosen = assemble.select(targets, done, SPEC)
    assert [record.id for record in chosen][-1] == "prose-mathlib-extra"

    def allowed(name: str) -> bool:
        return name not in {"Old.name", inside[2].declaration.name}

    pending = assemble.needed(targets, done, SPEC, allowed)
    mathlib = [
        t
        for t in pending
        if (t.query_type, t.declaration.library) == ("prose", "mathlib")
    ]
    assert len(mathlib) == 2 and inside[2] not in mathlib
    assert "prose-mathlib-extra" not in {
        r.id for r in assemble.select(targets, done, SPEC, allowed)
    }


def _records(count: int, groups: int) -> list[QueryRecord]:
    return [
        QueryRecord(
            id=f"q{i}",
            query=f"query {i}",
            query_type="prose" if i % 2 else "goal",
            variant="v",
            source="declaration",
            library="mathlib",
            area="Algebra",
            target=f"T{i}",
            judgments={f"T{i}": 3, f"U{i}": 1},
            group_id=f"g{i % groups}",
            track="human",
        )
        for i in range(count)
    ]


def test_splits_keep_groups_together_and_follow_the_share() -> None:
    spec = MixSpec(development_share=0.25)
    assigned = assemble.assign_splits(_records(80, 40), spec)
    assert [record.id for record in assigned] == sorted(f"q{i}" for i in range(80))
    split_of_group: dict[str, set[str]] = {}
    for record in assigned:
        split_of_group.setdefault(record.group_id, set()).add(record.split)
    assert all(len(splits) == 1 for splits in split_of_group.values())
    development = [record for record in assigned if record.split == "development"]
    assert len(development) == 20
    assert {record.split for record in assigned} == set(SPLITS)
    again = assemble.assign_splits(_records(80, 40), spec)
    assert [record.split for record in again] == [record.split for record in assigned]


def test_collection_matches_the_evaluator_format() -> None:
    assigned = assemble.assign_splits(_records(20, 20), MixSpec())
    collection = to_collection(assigned, "rev-1", "test")
    assert collection["corpus_revision"] == "rev-1"
    assert len(collection["queries"]) == 16
    query = collection["queries"][0]
    assert set(query) == {"id", "group_id", "track", "answerability", "judgments"}
    assert query["answerability"] == "answerable" and query["track"] == "human"


def test_summary_table_counts_by_bucket_and_library() -> None:
    table = assemble.summary_table(_records(6, 6))
    assert "| Query type | mathlib | Total |" in table
    assert "| goal | 3 | 3 |" in table
    assert "| prose | 3 | 3 |" in table
    assert table.rstrip().endswith("| Total | 6 | 6 |")
