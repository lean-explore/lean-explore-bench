import sqlite3
from pathlib import Path

from lean_explore_bench.builder.corpus import (
    Corpus,
    declared_kind,
    library_and_area,
    load_corpus,
    revision_of,
)


def test_library_and_area() -> None:
    assert library_and_area("Mathlib.Algebra.Group.Basic") == ("mathlib", "Algebra")
    assert library_and_area("Physlib.QFT.Basic") == ("physlib", "QFT")
    assert library_and_area("Init") == ("core", "root")
    assert library_and_area("Lean.Meta.Basic") is None
    assert library_and_area("Mathlib.Tactic.Ring") is None
    assert library_and_area("Batteries.Classes.Deprecated") is None
    assert library_and_area("Std.Data.DTreeMap.Internal.Lemmas") is None


def test_declared_kind_requires_the_source_to_introduce_the_name() -> None:
    assert declared_kind("Nat.add_comm", "theorem Nat.add_comm : True := trivial") == (
        "theorem"
    )
    assert declared_kind("Foo.bar", "/-- def baz -/\n@[simp] lemma bar : True") == (
        "theorem"
    )
    assert declared_kind("Foo.bar", "abbrev _root_.Foo.bar := 1") == "definition"
    assert declared_kind("Foo.Bar", "class Bar (a : Type) where") == "structure"
    assert declared_kind("Foo.Bar.field", "structure Bar where\n  field : Nat") is None
    assert declared_kind("Foo.inst", "instance : Add Nat := ⟨Nat.add⟩") is None


def test_load_corpus_keeps_only_eligible_declarations(
    corpus: Corpus, corpus_path: Path
) -> None:
    by_name = corpus.by_name()
    assert len(corpus.names) == 40
    assert len(corpus.eligible) == 34
    assert by_name["Demo.Algebra.double"].kind == "definition"
    assert by_name["Demo.Algebra.double"].docstring is None
    assert by_name["Demo.Algebra.Pair"].kind == "structure"
    assert by_name["Cslib.Demo.step_comm_0"].library == "cslib"
    for name in (
        "Demo.Algebra.Pair.left",
        "Demo.Tactic.helper_lemma",
        "Lean.Meta.internal_lemma",
        "Demo.Algebra.old_lemma",
        "Demo.Algebra.tiny",
        "Demo.Algebra.instAdd",
    ):
        assert name in corpus.names and name not in by_name
    assert corpus.modules["Demo.Algebra.Pair.left"] == "Mathlib.Algebra.Basic"
    assert corpus.revision.startswith("leanexplore:snapshot-1:")
    assert load_corpus(corpus_path, label="x").revision.startswith("leanexplore:x:")


def test_revision_ignores_order() -> None:
    assert revision_of("a", ["x", "y"]) == revision_of("a", ["y", "x"])
    assert revision_of("a", ["x", "y"]) != revision_of("a", ["x", "z"])


def test_established_names_need_the_same_module_in_the_older_snapshot(
    corpus_path: Path, tmp_path: Path
) -> None:
    older = tmp_path / "older" / "lean_explore.db"
    older.parent.mkdir()
    connection = sqlite3.connect(older)
    connection.execute("CREATE TABLE declarations (name TEXT, module TEXT)")
    connection.executemany(
        "INSERT INTO declarations VALUES (?, ?)",
        [
            ("Demo.Algebra.add_comm_3", "Mathlib.Algebra.Basic"),
            ("Demo.Algebra.add_comm_4", "Mathlib.Elsewhere"),
        ],
    )
    connection.commit()
    connection.close()
    corpus = load_corpus(corpus_path, established=older)
    assert corpus.established == frozenset({"Demo.Algebra.add_comm_3"})
    assert corpus.is_established("Demo.Algebra.add_comm_3")
    assert not corpus.is_established("Demo.Algebra.add_comm_4")
    assert load_corpus(corpus_path).is_established("anything")
