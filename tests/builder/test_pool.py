"""Tests for pooling engine results and adding the grades."""

import json
from pathlib import Path

import pytest

from lean_explore_bench.builder import cli, pool
from lean_explore_bench.builder.corpus import load_corpus, read_statements
from lean_explore_bench.record import QueryRecord, read_records, write_records
from lean_explore_bench.spec import MixSpec

TARGET = "Demo.Algebra.add_comm_3"
OTHER = "Demo.Algebra.add_comm_4"
THIRD = "Demo.Algebra.add_comm_5"


def _record(identifier: str, judgments: dict[str, int]) -> QueryRecord:
    return QueryRecord(
        id=identifier,
        query=f"query {identifier}",
        query_type="prose",
        variant="v",
        source="declaration",
        library="mathlib",
        area="Algebra",
        target=TARGET,
        judgments=judgments,
        group_id=identifier,
        split="test",
    )


RECORDS = [_record("q1", {TARGET: 3}), _record("q2", {TARGET: 3, OTHER: 1})]
RESULTS = {
    "one": {"q1": {"documents": [OTHER, TARGET, "Unknown.name"]}},
    "two": {"q1": {"documents": [THIRD, OTHER]}, "q2": {"documents": [TARGET, OTHER]}},
}


def test_statements_cover_ineligible_declarations(corpus_path: Path) -> None:
    found = read_statements(corpus_path, [TARGET, "Demo.Algebra.Pair.left", "Nope"], 20)
    assert set(found) == {TARGET, "Demo.Algebra.Pair.left"}
    assert all(len(text) <= 20 for text in found.values())


def test_tasks_hide_engine_and_rank_and_skip_labelled_names(corpus_path: Path) -> None:
    names = pool.pooled_names(RECORDS, RESULTS, limit=2)
    assert names == {"q1": {OTHER, TARGET, THIRD}, "q2": {TARGET, OTHER}}
    short = pool.pooled_names(RECORDS, RESULTS, until_answer=True)
    assert short == {"q1": {OTHER, THIRD}, "q2": set()}
    statements = read_statements(corpus_path, [TARGET, OTHER, THIRD])
    tasks = pool.tasks(RECORDS, pool.pooled_names(RECORDS, RESULTS), statements)
    assert [task["id"] for task in tasks] == ["q1"]
    task = tasks[0]
    assert [item["name"] for item in task["candidates"]] == [OTHER, THIRD]
    assert task["answers"][0]["name"] == TARGET and task["answers"][0]["grade"] == 3
    assert "theorem" in task["candidates"][0]["statement"]


def test_apply_adds_grades_without_changing_labels() -> None:
    graded = {"q1": {OTHER: 3, THIRD: 1, TARGET: 2}, "q2": {OTHER: 3}, "zz": {OTHER: 3}}
    first, second = pool.apply(RECORDS, graded, "judge")
    assert first.judgments == {TARGET: 3, OTHER: 3}
    assert first.provenance == {"pooled": [OTHER], "pool_judge": "judge"}
    assert second == RECORDS[1]


def test_pool_command_round_trip(
    corpus_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "mix"
    write_records(out / "queries.jsonl", RECORDS)
    (out / "runs").mkdir()
    for engine, results in RESULTS.items():
        lines = [json.dumps({"id": key, **value}) for key, value in results.items()]
        (out / "runs" / f"{engine}.jsonl").write_text("\n".join(lines) + "\n")
    common = ["pool", "--corpus", str(corpus_path), "--out", str(out)]
    tasks = tmp_path / "pool" / "tasks.jsonl"
    cli.main([*common, "--engine", "one", "two", "--to", str(tasks)])
    assert "Wrote 1 judging tasks" in capsys.readouterr().out
    task = json.loads(tasks.read_text())
    grades = tmp_path / "grades.jsonl"
    grades.write_text(json.dumps({"id": task["id"], "relevant": {OTHER: 2}}) + "\n\n")
    cli.main([*common, "--grades", str(grades), "--judge", "tester"])
    assert "Added 1 answers to 1 queries" in capsys.readouterr().out
    updated = read_records(out / "queries.jsonl")
    assert updated[0].judgments == {TARGET: 3, OTHER: 2}
    collection = json.loads((out / "collection.test.json").read_text())
    assert collection["queries"][0]["judgments"] == {TARGET: 3, OTHER: 2}
    assert load_corpus(corpus_path).revision == collection["corpus_revision"]


@pytest.mark.parametrize(("library", "written"), [("mathlib", 1), ("absent", 0)])
def test_balanced_pool_keeps_only_candidates_of_the_shape(
    corpus_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    library: str,
    written: int,
) -> None:
    out = tmp_path / "mix"
    write_records(out / "queries.jsonl", RECORDS)
    (out / "runs").mkdir()
    for engine, results in RESULTS.items():
        lines = [json.dumps({"id": key, **value}) for key, value in results.items()]
        (out / "runs" / f"{engine}.jsonl").write_text("\n".join(lines) + "\n")
    monkeypatch.setattr(cli, "balanced", lambda: MixSpec(library_counts={library: 1}))
    tasks = tmp_path / "tasks.jsonl"
    arguments = ["pool", "--corpus", str(corpus_path), "--out", str(out)]
    cli.main(
        [
            *arguments,
            "--engine",
            "one",
            "two",
            "--shape",
            "balanced",
            "--to",
            str(tasks),
        ]
    )
    assert f"Wrote {written} judging tasks" in capsys.readouterr().out
