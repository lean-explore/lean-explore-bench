import random

from lean_explore_bench.builder.corpus import Corpus, Declaration
from lean_explore_bench.builder.names import (
    VARIANT_WEIGHTS,
    name_query,
    spaced,
    suffix_index,
    typo,
)
from lean_explore_bench.builder.sample import Target


def _target(name: str) -> Target:
    declaration = Declaration(
        name, "Mathlib.Algebra.Basic", "mathlib", "Algebra", "theorem", None, "", None
    )
    return Target(declaration, "name", 0)


def test_spaced_splits_dots_underscores_and_camel_case() -> None:
    assert spaced("Nat.add_comm") == "Nat add comm"
    assert spaced("ContinuousLinearMap.comp") == "Continuous Linear Map comp"


def test_typo_changes_only_the_last_component() -> None:
    rng = random.Random(0)
    for _ in range(50):
        changed = typo("Nat.add_comm_assoc", rng)
        assert changed.startswith("Nat.")
        assert changed != "Nat.add_comm_assoc"
        assert len(changed) in {
            len("Nat.add_comm_assoc"),
            len("Nat.add_comm_assoc") - 1,
        }
    assert typo("Nat.add", rng) == "Nat.add"
    assert typo("add_comm", random.Random(1)).count(".") == 0


def test_suffix_index_includes_full_names() -> None:
    index = suffix_index(["A.b.c", "X.b.c", "c"])
    assert sorted(index["b.c"]) == ["A.b.c", "X.b.c"]
    assert sorted(index["c"]) == ["A.b.c", "X.b.c", "c"]
    assert index["A.b.c"] == ["A.b.c"]


def test_every_variant_is_produced_with_consistent_judgments(corpus: Corpus) -> None:
    index = suffix_index(corpus.names)
    rng = random.Random(3)
    seen: dict[str, str] = {}
    for declaration in corpus.eligible:
        record = name_query(Target(declaration, "name", 0), index, corpus.names, rng)
        seen[record.variant] = record.query
        assert record.judgments[record.target] == 3
        assert record.group_id == record.target == declaration.name
        if record.variant == "exact":
            assert record.query == declaration.name
        if record.variant == "suffix":
            assert declaration.name.endswith("." + record.query)
            assert set(record.judgments) == set(index[record.query])
    assert set(seen) == set(VARIANT_WEIGHTS)


def test_variants_that_cannot_apply_fall_back_to_exact() -> None:
    index = suffix_index(["Nat.add", "nat.add"] + [f"N{i}.add" for i in range(9)])
    names = frozenset(index)
    variants = set()
    rng = random.Random(0)
    for _ in range(200):
        record = name_query(_target("Nat.add"), index, names, rng)
        variants.add(record.variant)
        assert record.variant in {"exact", "spaced"}
        if record.variant == "exact":
            assert record.query == "Nat.add"
    assert variants == {"exact", "spaced"}
    single = name_query(_target("lonely"), suffix_index(["lonely"]), names, rng)
    assert single.query in {
        "lonely",
        "lonley",
        "lonly",
        "loenly",
        "lnely",
        "lonel",
    } or (single.variant in {"exact", "typo"})
