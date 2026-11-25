"""Write queries with one language model and check them with another.

For each target a writer model produces a query in a chosen variant. The
query must pass the rule checks, then a judge from a different model family
must grade the target 3 (a direct answer) and find the query specific. A
query that fails is rewritten, with the reason for the rejection, up to
twice; a target that fails three times is dropped and a reserve target takes its
place when the mix is assembled.

Finished targets are appended to a journal file, so an interrupted run
resumes where it stopped and nothing is paid for twice.
"""

import asyncio
import json
import random
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from lean_explore_bench.infra import OpenRouterClient
from lean_explore_bench.mix import checks, prompts
from lean_explore_bench.mix.record import QueryRecord
from lean_explore_bench.mix.sample import Target
from lean_explore_bench.mix.style import Style, draw_style

MAX_ATTEMPTS = 3


class BudgetExceededError(RuntimeError):
    """The run reached its spending limit."""


@dataclass(frozen=True)
class GenerationSettings:
    """Models and limits of a generation run.

    Attributes:
        writer_model: OpenRouter model that writes queries.
        judge_model: OpenRouter model that grades them; use another family.
        budget_usd: The run stops before starting a target once the client
            has spent this much.
        seed: Seed for variant and style choices.
        style_profile: Profile of real searches that styles are drawn from
            (see :mod:`lean_explore_bench.mix.profile`); None for typical
            values.
    """

    writer_model: str
    judge_model: str
    budget_usd: float = 25.0
    seed: int = 20261111
    style_profile: dict[str, Any] | None = None


def _rng(seed: int, target: Target, attempt: int) -> random.Random:
    return random.Random(f"{seed}:{target.id}:{attempt}")


def plan(
    settings: GenerationSettings, target: Target, attempt: int
) -> tuple[str, Style]:
    """Return the variant and style of one attempt at a target's query."""
    style = draw_style(
        target.query_type, settings.style_profile, _rng(settings.seed, target, 0)
    )
    variant = prompts.choose_variant(
        target.query_type, _rng(settings.seed, target, attempt + 1)
    )
    return variant, style


async def judge_written(
    client: OpenRouterClient,
    settings: GenerationSettings,
    target: Target,
    query: str,
    style: Style,
) -> dict[str, Any]:
    """Check a written query against the rules, then ask the judge."""
    declaration = target.declaration
    rule = checks.problem(
        query, target.query_type, declaration.name, declaration.docstring, style
    )
    if rule is not None:
        return {"accepted": False, "rule": rule}
    verdict = await client.complete_json(
        prompts.judge_messages(declaration, query),
        prompts.JUDGE_SCHEMA,
        name="verdict",
        model=settings.judge_model,
        temperature=0.0,
    )
    return {"accepted": verdict["grade"] == 3 and verdict["specific"], **verdict}


def _record(
    target: Target,
    query: str,
    variant: str,
    style: Style,
    settings: GenerationSettings,
    attempts: int,
) -> QueryRecord:
    declaration = target.declaration
    return QueryRecord(
        id=target.id,
        query=query,
        query_type=target.query_type,
        variant=variant,
        source="declaration",
        library=declaration.library,
        area=declaration.area,
        target=declaration.name,
        judgments={declaration.name: 3},
        group_id=declaration.name,
        track="unknown",
        provenance={
            "method": "language-model",
            "writer_model": settings.writer_model,
            "judge_model": settings.judge_model,
            "prompt_version": prompts.PROMPT_VERSION,
            "attempts": attempts,
            "style": style.to_json(),
        },
    )


def tasks(
    settings: GenerationSettings, targets: Iterable[Target]
) -> list[dict[str, str]]:
    """Return the writing task of every target, for a writer outside this run.

    Each task holds the target's identifier and the same instructions the
    built-in writer receives. Queries written for them are taken in by
    :func:`submit`.
    """
    result = []
    for target in targets:
        variant, style = plan(settings, target, 0)
        messages = prompts.writer_messages(
            target.declaration, target.query_type, variant, style
        )
        result.append({"id": target.id, "task": str(messages[1]["content"])})
    return result


async def submit(
    client: OpenRouterClient,
    settings: GenerationSettings,
    targets: Iterable[Target],
    written: dict[str, str],
    journal: Path,
    revise: bool = False,
) -> dict[str, dict[str, Any]]:
    """Check and judge queries written outside this run, one per target.

    Args:
        client: OpenRouter client, used for the judge only.
        settings: ``writer_model`` names whoever wrote the queries.
        targets: The targets the tasks were made from.
        written: The query written for each target identifier.
        journal: JSON Lines file that receives one entry per target.
        revise: Also take a query for a target that already has an accepted
            one, when the two differ. The new query replaces the old one
            only if it is accepted; otherwise the old one stays.

    Returns:
        Every journal entry, old and new, keyed by target identifier. A
        target whose first query fails is recorded as rejected, so a reserve
        target takes its place in the next round of tasks.
    """
    done = read_journal(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)

    async def run(target: Target) -> dict[str, Any] | None:
        variant, style = plan(settings, target, 0)
        earlier = done.get(target.id, {}).get("record")
        if earlier is not None:
            variant = earlier["variant"]
        query = written[target.id].strip()
        try:
            verdict = await judge_written(client, settings, target, query, style)
        except (KeyError, ValueError, jsonschema.ValidationError) as error:
            verdict = {"accepted": False, "error": type(error).__name__}
        if earlier is not None and not verdict["accepted"]:
            return None
        record = (
            _record(target, query, variant, style, settings, 1).to_json()
            if verdict["accepted"]
            else None
        )
        if record is not None and earlier is not None:
            record["provenance"]["revised_from"] = earlier["provenance"]["writer_model"]
        return {
            "id": target.id,
            "accepted": record is not None,
            "record": record,
            "attempts": [{"variant": variant, "query": query, **verdict}],
        }

    def wanted(target: Target) -> bool:
        if target.id not in written:
            return False
        entry = done.get(target.id)
        if entry is None:
            return True
        revised = (
            entry["accepted"] and entry["record"]["query"] != written[target.id].strip()
        )
        return revise and revised

    entries = await asyncio.gather(*(run(t) for t in targets if wanted(t)))
    with journal.open("a", encoding="utf-8") as file:
        for entry in entries:
            if entry is not None:
                done[entry["id"]] = entry
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return done


async def _attempt(
    client: OpenRouterClient,
    settings: GenerationSettings,
    target: Target,
    variant: str,
    style: Style,
    rejected: tuple[str, str] | None,
) -> tuple[str, dict[str, Any]]:
    """Write and judge one query; return it with the verdict."""
    written = await client.complete_json(
        prompts.writer_messages(
            target.declaration, target.query_type, variant, style, rejected
        ),
        prompts.WRITER_SCHEMA,
        name="query",
        model=settings.writer_model,
        temperature=0.9,
    )
    query = str(written["query"]).strip()
    return query, await judge_written(client, settings, target, query, style)


async def write_query(
    client: OpenRouterClient, settings: GenerationSettings, target: Target
) -> dict[str, Any]:
    """Write the query for one target, retrying after a rejection.

    Returns:
        A journal entry: the target's identifier, whether a query was
        accepted, the accepted record if any, and every attempt.
    """
    attempts: list[dict[str, Any]] = []
    record: QueryRecord | None = None
    rejected: tuple[str, str] | None = None
    for attempt in range(MAX_ATTEMPTS):
        variant, style = plan(settings, target, attempt)
        try:
            query, verdict = await _attempt(
                client, settings, target, variant, style, rejected
            )
        except (KeyError, ValueError, jsonschema.ValidationError) as error:
            attempts.append({"variant": variant, "error": type(error).__name__})
            continue
        attempts.append({"variant": variant, "query": query, **verdict})
        rejected = (query, verdict.get("rule", "the judge did not accept it"))
        if verdict["accepted"]:
            record = _record(target, query, variant, style, settings, attempt + 1)
            break
    return {
        "id": target.id,
        "accepted": record is not None,
        "record": record.to_json() if record is not None else None,
        "attempts": attempts,
    }


def read_journal(path: Path) -> dict[str, dict[str, Any]]:
    """Read finished journal entries, keyed by target identifier."""
    if not path.exists():
        return {}
    entries = (
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    return {entry["id"]: entry for entry in entries}


async def generate(
    client: OpenRouterClient,
    settings: GenerationSettings,
    targets: list[Target],
    journal: Path,
) -> dict[str, dict[str, Any]]:
    """Write queries for every target not yet in the journal.

    Args:
        client: OpenRouter client; its concurrency cap bounds the run.
        settings: Models, budget and seed.
        targets: Targets whose bucket is written by a language model.
        journal: JSON Lines file that receives one entry per finished target.

    Returns:
        Every journal entry, old and new, keyed by target identifier.

    Raises:
        BudgetExceededError: If the spending limit is reached. Entries
            written so far stay in the journal.
    """
    done = read_journal(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    lock = asyncio.Lock()

    async def run(target: Target) -> None:
        if client.usage.cost >= settings.budget_usd:
            raise BudgetExceededError(
                f"Spent ${client.usage.cost:.2f} of ${settings.budget_usd:.2f}"
            )
        entry = await write_query(client, settings, target)
        async with lock:
            done[entry["id"]] = entry
            with journal.open("a", encoding="utf-8") as file:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    pending = [target for target in targets if target.id not in done]
    results = await asyncio.gather(
        *(run(target) for target in pending), return_exceptions=True
    )
    failures = [result for result in results if isinstance(result, BaseException)]
    if failures:
        raise failures[0]
    return done
