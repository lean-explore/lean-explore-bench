import pytest

from lean_explore_bench.mix.assemble import assign_splits
from lean_explore_bench.mix.corpus import Corpus
from lean_explore_bench.mix.record import QueryRecord
from lean_explore_bench.mix.sample import sample_targets
from lean_explore_bench.mix.spec import (
    BALANCED_TOTALS,
    BUCKET_OF_FORM,
    BUCKET_SIZE,
    MixSpec,
    balanced,
)

SPEC = MixSpec(
    library_counts={"mathlib": 4, "cslib": 2},
    query_types=("name", "prose", "goal"),
    reserve=0.5,
)


def test_cells_hold_quota_plus_reserve_without_reuse(corpus: Corpus) -> None:
    targets = sample_targets(corpus, SPEC)
    names = [target.declaration.name for target in targets]
    assert len(names) == len(set(names))
    cells: dict[tuple[str, str], list[int]] = {}
    for target in targets:
        key = (target.query_type, target.declaration.library)
        cells.setdefault(key, []).append(target.order)
    assert cells[("name", "mathlib")] == list(range(6))
    assert cells[("goal", "cslib")] == list(range(2))
    assert all(
        target.declaration.kind == "theorem"
        for target in targets
        if target.query_type == "goal"
    )
    assert {target.declaration.area for target in targets} >= {"Algebra", "Topology"}


def test_sampling_is_deterministic_and_ids_are_stable(corpus: Corpus) -> None:
    first = sample_targets(corpus, SPEC)
    second = sample_targets(corpus, SPEC)
    assert [target.id for target in first] == [target.id for target in second]
    assert first[0].id.startswith("name-mathlib-")
    other = sample_targets(
        corpus, MixSpec(SPEC.library_counts, SPEC.query_types, reserve=0.5, seed=1)
    )
    assert [target.id for target in first] != [target.id for target in other]


def test_too_few_declarations_is_an_error(corpus: Corpus) -> None:
    with pytest.raises(ValueError, match="eligible declarations"):
        sample_targets(corpus, MixSpec(library_counts={"cslib": 9}))
    with pytest.raises(ValueError, match="eligible declarations"):
        sample_targets(corpus, MixSpec(library_counts={"flt": 1}))


def test_spec_validation() -> None:
    assert MixSpec().per_type == 200
    with pytest.raises(ValueError, match="Unknown query types"):
        MixSpec(query_types=("riddle",))
    with pytest.raises(ValueError, match="at least one"):
        MixSpec(library_counts={"mathlib": 0})
    with pytest.raises(ValueError, match="at least one"):
        MixSpec(library_counts={})
    with pytest.raises(ValueError, match="reserve"):
        MixSpec(reserve=-1)
    with pytest.raises(ValueError, match="development_share"):
        MixSpec(development_share=1.0)


def test_larger_buckets_add_targets_without_changing_the_uniform_ones(
    corpus: Corpus,
) -> None:
    uniform = MixSpec(library_counts={"mathlib": 2, "cslib": 1}, query_types=("prose",))
    larger = MixSpec(
        library_counts={"mathlib": 2, "cslib": 1},
        query_types=("prose",),
        type_totals={"prose": 6},
    )
    before = [target.id for target in sample_targets(corpus, uniform)]
    after = [target.id for target in sample_targets(corpus, larger)]
    assert set(before) < set(after) and len(after) == len(set(after)) == 12


def test_balanced_shape_has_equal_buckets() -> None:
    spec = balanced()
    assert spec.type_totals == BALANCED_TOTALS
    per_bucket: dict[str, int] = {}
    for form, total in BALANCED_TOTALS.items():
        bucket = BUCKET_OF_FORM[form]
        per_bucket[bucket] = per_bucket.get(bucket, 0) + total
        spread = [spec.count(form, library) for library in spec.library_counts]
        assert sum(spread) == total
    assert set(per_bucket.values()) == {BUCKET_SIZE}
    assert list(spec.library_counts) == ["mathlib"]
    assert spec.count("goal", "mathlib") == 320
    assert spec.draw_counts == MixSpec().draw_counts
    assert MixSpec().count("goal", "flt") == 20
    assert "quantuminfo" in MixSpec().draw_counts
    assert "quantuminfo" not in MixSpec().library_counts


def test_a_group_too_large_for_development_stays_in_test() -> None:
    def record(identifier: str, group: str) -> QueryRecord:
        return QueryRecord(
            id=identifier,
            query="q",
            query_type="prose",
            variant="v",
            source="declaration",
            library="mathlib",
            area="A",
            target="T",
            judgments={"T": 3},
            group_id=group,
        )

    records = [record(f"a{i}", "big") for i in range(3)]
    records += [record(f"b{i}", f"g{i}") for i in range(7)]
    assigned = assign_splits(records, MixSpec())
    development = [item for item in assigned if item.split == "development"]
    assert len(development) == 2
    assert all(item.group_id != "big" for item in development)
