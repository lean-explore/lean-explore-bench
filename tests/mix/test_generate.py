import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from mix_helpers import scripted_client, system_of, user_of

from lean_explore_bench.mix import prompts
from lean_explore_bench.mix.corpus import Corpus
from lean_explore_bench.mix.generate import (
    BudgetExceededError,
    GenerationSettings,
    generate,
    read_journal,
    write_query,
)
from lean_explore_bench.mix.sample import Target

SETTINGS = GenerationSettings(writer_model="test/writer", judge_model="test/judge")
GOOD = "the sum of two natural numbers does not depend on their order"


def _targets(corpus: Corpus, count: int) -> list[Target]:
    theorems = [d for d in corpus.eligible if d.kind == "theorem"]
    return [Target(theorems[i], "prose", i) for i in range(count)]


def _model(queries: list[str], verdict: dict[str, Any]) -> Any:
    """Writer replies with ``queries`` in turn; judge always gives ``verdict``."""
    remaining = list(queries)

    def respond(body: dict[str, Any]) -> str:
        if system_of(body) == prompts.JUDGE_SYSTEM:
            assert body["model"] == "test/judge"
            return json.dumps(verdict)
        assert body["model"] == "test/writer"
        return remaining.pop(0)

    return respond


def test_accepted_query_becomes_a_record(corpus: Corpus) -> None:
    target = _targets(corpus, 1)[0]
    client = scripted_client(
        _model([json.dumps({"query": f" {GOOD} "})], {"grade": 3, "specific": True})
    )
    entry = asyncio.run(write_query(client, SETTINGS, target))
    assert entry["accepted"] and entry["id"] == target.id
    record = entry["record"]
    assert record["query"] == GOOD
    assert record["judgments"] == {target.declaration.name: 3}
    assert record["group_id"] == record["target"] == target.declaration.name
    assert record["track"] == "unknown"
    assert record["provenance"]["attempts"] == 1
    assert record["provenance"]["style"]["words"] == 12
    assert record["provenance"]["prompt_version"] == prompts.PROMPT_VERSION
    assert len(entry["attempts"]) == 1


def test_rule_failure_is_retried_with_the_reason(corpus: Corpus) -> None:
    target = _targets(corpus, 1)[0]
    seen: list[str] = []

    def respond(body: dict[str, Any]) -> str:
        if system_of(body) == prompts.JUDGE_SYSTEM:
            return json.dumps({"grade": 3, "specific": True})
        seen.append(user_of(body))
        query = "too short" if len(seen) == 1 else GOOD
        return json.dumps({"query": query})

    entry = asyncio.run(write_query(scripted_client(respond), SETTINGS, target))
    assert entry["accepted"]
    assert entry["attempts"][0]["rule"] == "reads as keywords, not prose"
    assert "rejected (reads as keywords, not prose)" in seen[1]
    assert entry["record"]["provenance"]["attempts"] == 2


@pytest.mark.parametrize(
    "verdict", [{"grade": 2, "specific": True}, {"grade": 3, "specific": False}]
)
def test_judge_rejection_drops_the_target(
    corpus: Corpus, verdict: dict[str, Any]
) -> None:
    target = _targets(corpus, 1)[0]
    client = scripted_client(_model([json.dumps({"query": GOOD})] * 3, verdict))
    entry = asyncio.run(write_query(client, SETTINGS, target))
    assert not entry["accepted"] and entry["record"] is None
    assert [attempt["accepted"] for attempt in entry["attempts"]] == [False] * 3


def test_invalid_model_output_counts_as_a_failed_attempt(corpus: Corpus) -> None:
    target = _targets(corpus, 1)[0]
    client = scripted_client(
        _model(
            ["not json", json.dumps({"wrong": 1}), "[]"],
            {"grade": 3, "specific": True},
        )
    )
    entry = asyncio.run(write_query(client, SETTINGS, target))
    assert not entry["accepted"]
    assert [attempt["error"] for attempt in entry["attempts"]] == [
        "JSONDecodeError",
        "ValidationError",
        "ValidationError",
    ]


def test_style_is_drawn_from_the_profile(corpus: Corpus) -> None:
    theorem = next(d for d in corpus.eligible if d.kind == "theorem")
    profile = {"forms": {"keywords": {"words": {"4": 1.0}, "marks": {}}}}
    settings = GenerationSettings("test/writer", "test/judge", style_profile=profile)
    seen: list[str] = []

    def respond(body: dict[str, Any]) -> str:
        if system_of(body) == prompts.JUDGE_SYSTEM:
            return json.dumps({"grade": 3, "specific": True})
        seen.append(user_of(body))
        words = "addition order natural numbers swapped operands unchanged result"
        return json.dumps({"query": words if len(seen) == 1 else "addition order swap"})

    target = Target(theorem, "keywords", 0)
    entry = asyncio.run(write_query(scripted_client(respond), settings, target))
    assert "Use about 4 words" in seen[0]
    assert entry["attempts"][0]["rule"] == "8 words where 2 to 6 were asked for"
    assert entry["record"]["query"] == "addition order swap"
    assert entry["record"]["provenance"]["style"]["words"] == 4


def test_generate_journals_and_resumes(corpus: Corpus, tmp_path: Path) -> None:
    journal = tmp_path / "out" / "journal.jsonl"
    targets = _targets(corpus, 3)
    calls = {"writer": 0}

    def respond(body: dict[str, Any]) -> str:
        if system_of(body) == prompts.JUDGE_SYSTEM:
            return json.dumps({"grade": 3, "specific": True})
        calls["writer"] += 1
        return json.dumps({"query": GOOD})

    assert read_journal(journal) == {}
    done = asyncio.run(
        generate(scripted_client(respond), SETTINGS, targets[:2], journal)
    )
    assert set(done) == {target.id for target in targets[:2]}
    assert calls["writer"] == 2
    done = asyncio.run(generate(scripted_client(respond), SETTINGS, targets, journal))
    assert calls["writer"] == 3
    assert set(done) == set(read_journal(journal)) == {t.id for t in targets}
    assert len(journal.read_text().splitlines()) == 3


def test_generate_stops_at_the_budget(corpus: Corpus, tmp_path: Path) -> None:
    journal = tmp_path / "journal.jsonl"
    settings = GenerationSettings("test/writer", "test/judge", budget_usd=0.0)
    client = scripted_client(_model([], {"grade": 3, "specific": True}))
    with pytest.raises(BudgetExceededError, match="Spent"):
        asyncio.run(generate(client, settings, _targets(corpus, 1), journal))
    assert read_journal(journal) == {}
