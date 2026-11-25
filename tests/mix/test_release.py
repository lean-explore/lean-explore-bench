"""Tests for the published form of the benchmark."""

import json
from pathlib import Path

import pytest

from lean_explore_bench.mix import cli, release
from lean_explore_bench.mix.record import QueryRecord, write_records


def _record(name: str, **changes: object) -> QueryRecord:
    values: dict[str, object] = {
        "id": name,
        "query": f"query for {name}",
        "query_type": "prose",
        "variant": "prose",
        "source": "declaration",
        "library": "mathlib",
        "area": "Algebra",
        "target": "Alpha.beta",
        "judgments": {"Alpha.beta": 3, "Alpha.gamma": 2, "Alpha.delta": 1},
        "group_id": name,
        "provenance": {
            "method": "language-model",
            "writer_model": "writer",
            "judge_model": "judge",
            "pool_judge": "grader",
            "pooled": ["Alpha.gamma"],
            "revised_from": "earlier",
        },
        "split": "test",
    }
    values.update(changes)
    return QueryRecord.from_json(values)


def _thread(name: str, blinding: str | None, split: str = "test") -> QueryRecord:
    provenance = {"method": "contributed", "url": "https://example.org/thread"}
    if blinding is not None:
        provenance["blinding"] = blinding
    return _record(
        name,
        query_type="question",
        source="zulip",
        provenance=provenance,
        split=split,
    )


def test_row_holds_only_what_using_the_benchmark_needs() -> None:
    assert release.to_row(_record("a")) == {
        "id": release.public_id("a"),
        "query": "query for a",
        "bucket": "natural language",
        "form": "prose",
        "split": "test",
        "answers": [
            {"name": "Alpha.beta", "grade": 3},
            {"name": "Alpha.gamma", "grade": 2},
            {"name": "Alpha.delta", "grade": 1},
        ],
    }
    assert release.to_row(_thread("t", None))["bucket"] == "real questions"


def test_row_round_trip_keeps_what_scoring_uses() -> None:
    record = _record("a")

    restored = release.from_row(release.to_row(record))

    assert restored.judgments == record.judgments
    assert (restored.id, restored.query, restored.query_type, restored.split) == (
        release.public_id(record.id),
        record.query,
        record.query_type,
        record.split,
    )
    assert (restored.source, restored.target) == ("declaration", "Alpha.beta")
    assert release.from_row(release.to_row(_thread("t", None))).source == "zulip"


def test_published_identifier_is_stable_and_opaque() -> None:
    identifier = release.public_id("rewrite-zulip-123456")

    assert identifier == release.public_id("rewrite-zulip-123456")
    assert (
        len(identifier) == 12
        and "zulip" not in identifier
        and "123456" not in identifier
    )


def test_export_refuses_colliding_identifiers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build = _build(tmp_path, [_record("a"), _record("b")], ["a", "b"])
    monkeypatch.setattr(release, "public_id", lambda working_id: "same")

    with pytest.raises(ValueError, match="same published identifier"):
        release.export(build, tmp_path / "out", [])


def _build(tmp_path: Path, records: list[QueryRecord], run_ids: list[str]) -> Path:
    build = tmp_path / "build"
    write_records(build / "queries.jsonl", records)
    (build / "runs").mkdir()
    lines = [
        json.dumps(
            {"id": key, "status": "ok", "limit": 10, "documents": ["Alpha.beta"]}
        )
        for key in run_ids
    ]
    (build / "runs" / "engine.jsonl").write_text("\n".join(lines) + "\n")
    return build


def test_export_writes_splits_and_runs_that_load_back(tmp_path: Path) -> None:
    records = [_record("a"), _record("b", split="development"), _thread("t", None)]
    build = _build(tmp_path, records, ["t", "b", "a"])
    to = tmp_path / "published"

    counts = release.export(build, to, ["engine"])

    assert counts == {
        "queries/development.jsonl": 1,
        "queries/test.jsonl": 2,
        "runs/engine.jsonl": 3,
    }
    run = [json.loads(line) for line in (to / "runs" / "engine.jsonl").open()]
    public = sorted(release.public_id(name) for name in "abt")
    assert [row["id"] for row in run] == public
    assert run[0] == {"id": public[0], "documents": ["Alpha.beta"]}
    loaded = release.load_queries(to)
    assert sorted(record.id for record in loaded) == public
    assert release.load_queries(build) == sorted(records, key=lambda r: r.id)
    assert release.load_queries(tmp_path / "nowhere") == []


def test_export_refuses_unsplit_queries_and_incomplete_runs(tmp_path: Path) -> None:
    unsplit = _build(tmp_path / "one", [_record("a", split="")], ["a"])
    with pytest.raises(ValueError, match="no split"):
        release.export(unsplit, tmp_path / "out", [])
    partial = _build(tmp_path / "two", [_record("a"), _record("b")], ["a"])
    with pytest.raises(ValueError, match="no result for 1"):
        release.export(partial, tmp_path / "out", ["engine"])


def test_export_command_copies_the_card_and_scores_from_the_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    build = _build(tmp_path, [_record("a"), _thread("t", None)], ["a", "t"])
    card = tmp_path / "card.md"
    card.write_text("# Card\n")
    to = tmp_path / "published"

    cli.main(
        ["export", "--out", str(build), "--to", str(to), "--engine", "engine"]
        + ["--card", str(card)]
    )
    cli.main(["score", "--out", str(to), "--engine", "engine", "--split", "test"])

    assert (to / "README.md").read_text() == "# Card\n"
    output = capsys.readouterr().out
    assert "queries/test.jsonl: 2 rows" in output
    scores = json.loads((to / "scores" / "engine.test.json").read_text())
    assert scores["overall"]["success@1"] == 1.0
