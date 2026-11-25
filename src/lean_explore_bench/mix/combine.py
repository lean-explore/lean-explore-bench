"""Bring contributed queries into the mix, on the same footing as its own.

A contributed query arrives with proposed answers that nobody has graded.
The judge that accepted the mix's own queries grades each proposed answer,
and a query is kept when at least one answer is useful as it stands or with
a clear adaptation (grade 2 or 3).

In the balanced shape accepted thread queries form the ``real questions``
bucket: the contributed ones, and the mix's own from Zulip threads. Two
queries from the same thread share a group, so they stay in the same split.
"""

import asyncio
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from lean_explore_bench.infra import OpenRouterClient
from lean_explore_bench.mix import prompts
from lean_explore_bench.mix.corpus import Corpus, library_and_area
from lean_explore_bench.mix.generate import GenerationSettings, read_journal
from lean_explore_bench.mix.record import QueryRecord

MAX_TARGETS = 5
BATCH = 50
DISCUSSION_ORIGINS = frozenset({"discussion-rewrite", "synthetic_discussion_pilot"})
"""Origins whose queries were derived from a public discussion thread."""


@dataclass(frozen=True)
class Contributed:
    """One contributed query, before grading.

    Attributes:
        id: Stable identifier.
        query: The query text.
        targets: Proposed answers, ungraded.
        group_id: Queries that share a group are not independent.
        origin: The collection the query came from.
        blinding: Whether the writer had seen the answers, as recorded.
    """

    id: str
    query: str
    targets: tuple[str, ...]
    group_id: str
    origin: str
    blinding: str


def _from_row(row: dict[str, Any]) -> Contributed:
    if "sources" in row:
        sources = row["sources"]
        targets = [name for source in sources for name in source.get("targets") or []]
        first = sources[0]
        group = first.get("group") or row["request_id"][:12]
        return Contributed(
            id=f"contributed-{row['request_id'][:12]}",
            query=row["query"],
            targets=tuple(dict.fromkeys(targets)),
            group_id=f"{first['source']}:{group}",
            origin=first["source"],
            blinding=(first.get("generation") or {}).get("generation_blinding", ""),
        )
    message = row["source_id"].rsplit("-", 1)[-1]
    return Contributed(
        id=f"rewrite-zulip-{message}",
        query=row["query"],
        targets=tuple(dict.fromkeys(row.get("targets") or [])),
        group_id=f"zulip:{message}",
        origin="discussion-rewrite",
        blinding=(row.get("generation") or {}).get("generation_blinding", ""),
    )


def read_contributed(path: Path) -> list[Contributed]:
    """Read contributed queries from a JSON Lines file.

    Two layouts are accepted: one query per discussion thread (``source_id``,
    ``query``, ``targets``), and one request with its source memberships
    (``request_id``, ``query``, ``sources``, each with its own ``targets``).
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    return [_from_row(json.loads(line)) for line in lines if line.strip()]


async def _grade_one(
    client: OpenRouterClient,
    settings: GenerationSettings,
    item: Contributed,
    corpus: Corpus,
    by_name: dict[str, Any],
) -> dict[str, Any]:
    """Grade one contributed query and turn it into a journal entry."""
    entry: dict[str, Any] = {"id": item.id, "accepted": False, "record": None}
    targets = [name for name in item.targets if name in by_name][:MAX_TARGETS]
    if not targets:
        return {**entry, "reason": "no proposed answer is an eligible declaration"}
    if any(name.lower() in item.query.lower() for name in item.targets):
        return {**entry, "reason": "the query names an answer"}
    try:
        verdicts = await asyncio.gather(
            *(
                client.complete_json(
                    prompts.judge_messages(by_name[name], item.query),
                    prompts.JUDGE_SCHEMA,
                    name="verdict",
                    model=settings.judge_model,
                    temperature=0.0,
                )
                for name in targets
            )
        )
    except (KeyError, ValueError, jsonschema.ValidationError) as error:
        return {**entry, "reason": type(error).__name__}
    grades = {name: verdict["grade"] for name, verdict in zip(targets, verdicts)}
    judgments = {name: grade for name, grade in grades.items() if grade >= 1}
    best = max(grades, key=lambda name: grades[name])
    if grades[best] < 2:
        return {**entry, "reason": "the judge rejected every answer", "grades": grades}
    placed = library_and_area(corpus.modules[best])
    group = "zulip" if item.origin in DISCUSSION_ORIGINS else "pilot"
    record = QueryRecord(
        id=item.id,
        query=item.query,
        query_type="question",
        variant=item.origin,
        source=group,
        library=placed[0] if placed else "other",
        area=placed[1] if placed else "other",
        target=best,
        judgments=judgments,
        group_id=item.group_id,
        track="human",
        provenance={
            "method": "contributed",
            "origin": item.origin,
            "blinding": item.blinding,
            "judge_model": settings.judge_model,
            "judge_grade": grades[best],
        },
    )
    return {**entry, "accepted": True, "record": record.to_json()}


async def grade(
    client: OpenRouterClient,
    settings: GenerationSettings,
    items: Sequence[Contributed],
    corpus: Corpus,
    journal: Path,
) -> dict[str, dict[str, Any]]:
    """Grade every contributed query not yet in the journal.

    The run stops before a batch once the client has spent the budget; a
    later call resumes from the journal.

    Returns:
        Every journal entry, old and new, keyed by identifier.
    """
    done = read_journal(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    by_name = corpus.by_name()
    pending = [item for item in items if item.id not in done]
    for start in range(0, len(pending), BATCH):
        if client.usage.cost >= settings.budget_usd:
            break
        entries = await asyncio.gather(
            *(
                _grade_one(client, settings, item, corpus, by_name)
                for item in pending[start : start + BATCH]
            )
        )
        with journal.open("a", encoding="utf-8") as file:
            for entry in entries:
                done[entry["id"]] = entry
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return done


def thread_records(
    own: Iterable[QueryRecord], contributed: Iterable[QueryRecord], limit: int
) -> list[QueryRecord]:
    """Return the thread queries of the mix, as its ``question`` records.

    Contributed queries are all kept when they fit; the mix's own fill the
    rest, in the order given, up to ``limit`` in all.

    Args:
        own: The mix's own accepted Zulip queries.
        contributed: Accepted contributed queries, from :func:`grade`.
        limit: Most thread queries to return.
    """
    chosen = [*contributed, *own][:limit]
    return [
        QueryRecord.from_json({**record.to_json(), "query_type": "question"})
        for record in chosen
    ]
