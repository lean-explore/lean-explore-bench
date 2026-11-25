"""Tests for grading contributed queries and merging them into the mix."""

import asyncio
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from helpers import scripted_client, user_of

from lean_explore_bench.builder import cli, combine
from lean_explore_bench.builder.corpus import Corpus
from lean_explore_bench.builder.generate import GenerationSettings
from lean_explore_bench.builder.llm import OpenRouterSettings
from lean_explore_bench.record import QueryRecord, read_records
from lean_explore_bench.spec import MixSpec

TARGET = "Demo.Algebra.add_comm_3"
OTHER = "Demo.Algebra.add_comm_4"
SETTINGS = GenerationSettings(writer_model="", judge_model="judge", budget_usd=1.0)


def _thread(message: int, query: str, targets: list[str]) -> dict[str, Any]:
    return {
        "source_id": f"zulip-{message}",
        "query": query,
        "targets": targets,
        "generation": {"generation_blinding": "question_before_answers"},
    }


def _request(source: str, query: str, targets: list[str]) -> dict[str, Any]:
    return {
        "request_id": "abcdef0123456789",
        "query": query,
        "sources": [{"source": source, "group": "g1", "targets": targets}],
    }


def _write(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n\n")
    return path


def _grades(by_target: dict[str, int]) -> Any:
    def respond(body: dict[str, Any]) -> str:
        name = user_of(body).split("Name: ", 1)[1].split("\n", 1)[0]
        return json.dumps({"grade": by_target[name], "specific": True})

    return respond


def _grade(
    corpus: Corpus, tmp_path: Path, rows: list[dict[str, Any]], respond: Any
) -> dict[str, dict[str, Any]]:
    items = combine.read_contributed(_write(tmp_path / "in.jsonl", rows))
    client = scripted_client(respond)
    journal = tmp_path / "journal.jsonl"
    return asyncio.run(combine.grade(client, SETTINGS, items, corpus, journal))


def _record(identifier: str, query: str, source: str, bucket: str) -> QueryRecord:
    return QueryRecord(
        id=identifier,
        query=query,
        query_type=bucket,
        variant="v",
        source=source,
        library="mathlib",
        area="Algebra",
        target=TARGET,
        judgments={TARGET: 3},
        group_id=identifier,
        split="test",
    )


def test_both_layouts_are_read() -> None:
    thread = combine._from_row(_thread(7, "q", [TARGET, TARGET]))
    assert thread.id == "rewrite-zulip-7" and thread.group_id == "zulip:7"
    assert thread.targets == (TARGET,) and thread.origin == "discussion-rewrite"
    request = combine._from_row(_request("development_pilot", "q", [TARGET]))
    assert request.id == "contributed-abcdef012345"
    assert request.group_id == "development_pilot:g1" and request.blinding == ""


def test_accepted_query_keeps_graded_answers(corpus: Corpus, tmp_path: Path) -> None:
    rows = [_thread(7, "why does the sum of two numbers commute", [TARGET, OTHER])]
    done = _grade(corpus, tmp_path, rows, _grades({TARGET: 3, OTHER: 0}))
    record = QueryRecord.from_json(done["rewrite-zulip-7"]["record"])
    assert record.query_type == "question" and record.source == "zulip"
    assert record.target == TARGET and record.judgments == {TARGET: 3}
    assert record.provenance["judge_grade"] == 3


def test_pilot_queries_form_their_own_group(corpus: Corpus, tmp_path: Path) -> None:
    rows = [_request("development_pilot", "addition commutes naturals", [TARGET])]
    done = _grade(corpus, tmp_path, rows, _grades({TARGET: 2}))
    record = QueryRecord.from_json(next(iter(done.values()))["record"])
    assert record.query_type == "question" and record.source == "pilot"


@pytest.mark.parametrize(
    ("query", "targets", "grade", "reason"),
    [
        ("sum commutes", ["Missing.name"], 3, "no proposed answer"),
        (f"is {TARGET} what I want", [TARGET], 3, "names an answer"),
        ("sum commutes", [TARGET], 1, "rejected every answer"),
    ],
)
def test_rejections(
    corpus: Corpus,
    tmp_path: Path,
    query: str,
    targets: list[str],
    grade: int,
    reason: str,
) -> None:
    done = _grade(
        corpus, tmp_path, [_thread(1, query, targets)], _grades({TARGET: grade})
    )
    entry = done["rewrite-zulip-1"]
    assert not entry["accepted"] and reason in entry["reason"]


def test_bad_judge_reply_is_recorded_and_grading_resumes(
    corpus: Corpus, tmp_path: Path
) -> None:
    rows = [_thread(1, "sum commutes", [TARGET])]
    done = _grade(corpus, tmp_path, rows, lambda body: "{}")
    assert done["rewrite-zulip-1"]["reason"] == "ValidationError"

    def fail(body: dict[str, Any]) -> str:
        raise AssertionError("already graded")

    assert _grade(corpus, tmp_path, rows, fail) == done


def test_grading_stops_at_the_budget(corpus: Corpus, tmp_path: Path) -> None:
    items = combine.read_contributed(
        _write(tmp_path / "in.jsonl", [_thread(1, "sum commutes", [TARGET])])
    )
    broke = GenerationSettings(writer_model="", judge_model="j", budget_usd=0.0)
    client = scripted_client(_grades({TARGET: 3}))
    journal = tmp_path / "journal.jsonl"
    assert asyncio.run(combine.grade(client, broke, items, corpus, journal)) == {}


def test_thread_records_prefer_contributed_up_to_the_limit() -> None:
    prose = "why does the sum of two numbers commute"
    own = [_record(f"question-zulip-{i}", prose, "zulip", "question") for i in (1, 2)]
    contributed = [
        _record("rewrite-zulip-1", prose, "zulip", "question"),
        _record("contributed-1", "Nat.add_comm", "pilot", "question"),
    ]
    records = combine.thread_records(own, contributed, 3)
    assert [record.id for record in records] == [
        "rewrite-zulip-1",
        "contributed-1",
        "question-zulip-1",
    ]
    assert {record.query_type for record in records} == {"question"}


def test_contribute_then_balanced_build(
    corpus_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        OpenRouterSettings,
        "from_env",
        classmethod(lambda cls: OpenRouterSettings(api_key="k")),
    )
    monkeypatch.setattr(
        cli, "OpenRouterClient", lambda _settings: scripted_client(_grades({TARGET: 3}))
    )
    small = MixSpec(
        library_counts={"mathlib": 2},
        query_types=("name",),
        type_totals={"name": 3},
    )
    monkeypatch.setattr(cli, "balanced", lambda: small)
    rows = [_thread(7, "why does the sum of two numbers commute", [TARGET])]
    out = tmp_path / "out"
    common = ["--corpus", str(corpus_path), "--out", str(out)]
    cli.main(
        ["contribute", *common, "--queries", str(_write(tmp_path / "in.jsonl", rows))]
    )
    assert "Accepted 1 of 1 contributed queries" in capsys.readouterr().out
    cli.main(["build", *common, "--shape", "balanced"])
    records = read_records(out / "queries.jsonl")
    assert Counter(record.query_type for record in records) == {
        "name": 3,
        "question": 1,
    }
    thread = next(record for record in records if record.source == "zulip")
    assert thread.id == "rewrite-zulip-7" and thread.split in {"development", "test"}
