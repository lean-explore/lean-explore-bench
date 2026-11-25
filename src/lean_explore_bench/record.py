"""The record stored for every benchmark query."""

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SPLITS = ("development", "test")


@dataclass(frozen=True)
class QueryRecord:
    """One benchmark query with its known answers and provenance.

    Attributes:
        id: Stable identifier.
        query: The query text sent to a search engine.
        query_type: The bucket, for example ``informal``.
        variant: How the query was written within its bucket, for example
            ``typo`` for a name query.
        source: Where the query came from: ``declaration`` for a query
            written from a sampled declaration, ``zulip`` for a question
            asked on the Lean Zulip.
        library: Library of the target declaration.
        area: Area of the target declaration within its library.
        target: Name of the declaration the query was written for.
        judgments: Relevance grade (0 to 3) of every judged declaration.
        group_id: Queries that share a group are not independent and stay in
            the same split.
        track: ``human`` or ``agent``, the kind of searcher the query models.
        provenance: How the query was produced: models, prompt version,
            judge verdict or source link.
        split: ``development`` or ``test``; empty until assigned.
    """

    id: str
    query: str
    query_type: str
    variant: str
    source: str
    library: str
    area: str
    target: str
    judgments: dict[str, int]
    group_id: str
    track: str = "unknown"
    provenance: dict[str, Any] = field(default_factory=dict)
    split: str = ""

    def to_json(self) -> dict[str, Any]:
        """Return the record as a JSON object."""
        return asdict(self)

    @classmethod
    def from_json(cls, value: dict[str, Any]) -> "QueryRecord":
        """Build a record from a JSON object."""
        return cls(**value)


def write_records(path: Path, records: Iterable[QueryRecord]) -> None:
    """Write records as JSON Lines, one per line, sorted by identifier."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(record.to_json(), ensure_ascii=False, sort_keys=True)
        for record in sorted(records, key=lambda record: record.id)
    ]
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")


def read_records(path: Path) -> list[QueryRecord]:
    """Read records from a JSON Lines file; a missing file is empty."""
    if not path.exists():
        return []
    return [
        QueryRecord.from_json(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def to_collection(
    records: Iterable[QueryRecord], corpus_revision: str, split: str
) -> dict[str, Any]:
    """Export one split in the evaluator's collection format."""
    queries = [
        {
            "id": record.id,
            "group_id": record.group_id,
            "track": record.track,
            "answerability": "answerable",
            "judgments": record.judgments,
        }
        for record in records
        if record.split == split
    ]
    return {"corpus_revision": corpus_revision, "split": split, "queries": queries}
