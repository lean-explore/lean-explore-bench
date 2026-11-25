"""The published form of the benchmark.

A build directory holds ``queries.jsonl`` with every working field. The
published dataset holds only what is needed to use the benchmark:
``queries/<split>.jsonl``, one row per query with its graded answers, and
``runs/<engine>.jsonl``, the declarations each engine returned.

:func:`load_queries` reads either layout, so the published dataset can be
scored directly.
"""

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from lean_explore_bench.mix.assemble import SPLITS
from lean_explore_bench.mix.record import QueryRecord, read_records
from lean_explore_bench.mix.spec import BUCKET_OF_FORM, THREAD_BUCKET


def public_id(working_id: str) -> str:
    """Return the published identifier of a query.

    Working identifiers say how a query was made and, for thread queries,
    which message it came from. The published one is a hash of it: stable
    across exports and carrying no meaning.
    """
    return hashlib.sha256(working_id.encode()).hexdigest()[:12]


def to_row(record: QueryRecord) -> dict[str, Any]:
    """Return the published row of one query, with its answers best first."""
    answers = [
        {"name": name, "grade": grade}
        for name, grade in sorted(
            record.judgments.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    return {
        "id": public_id(record.id),
        "query": record.query,
        "bucket": BUCKET_OF_FORM.get(record.query_type, THREAD_BUCKET),
        "form": record.query_type,
        "split": record.split,
        "answers": answers,
    }


def from_row(row: dict[str, Any]) -> QueryRecord:
    """Build the working record of a published row.

    The published row holds only what scoring needs, so the fields it lacks
    are filled in: the first answer is the target and every query is its own
    group.
    """
    return QueryRecord(
        id=row["id"],
        query=row["query"],
        query_type=row["form"],
        variant="",
        source="zulip" if row["bucket"] == THREAD_BUCKET else "declaration",
        library="mathlib",
        area="",
        target=row["answers"][0]["name"],
        judgments={answer["name"]: answer["grade"] for answer in row["answers"]},
        group_id=row["id"],
        split=row["split"],
    )


def _read_rows(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def load_queries(directory: Path) -> list[QueryRecord]:
    """Read the queries of a build directory or of the published dataset."""
    build = directory / "queries.jsonl"
    if build.exists():
        return read_records(build)
    return [
        from_row(row)
        for split in SPLITS
        if (directory / "queries" / f"{split}.jsonl").exists()
        for row in _read_rows(directory / "queries" / f"{split}.jsonl")
    ]


def _write_rows(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")


def export(build: Path, to: Path, engines: Iterable[str]) -> dict[str, int]:
    """Write the published dataset from a build directory.

    Args:
        build: Directory with ``queries.jsonl`` and ``runs/``.
        to: Directory to write; existing files of the same name are replaced.
        engines: Engines whose runs are published.

    Returns:
        The number of rows written to each file, by path relative to ``to``.

    Raises:
        ValueError: If a query has no split, a run lacks a query, or two
            queries get the same published identifier.
    """
    records = sorted(
        read_records(build / "queries.jsonl"), key=lambda r: public_id(r.id)
    )
    if len({public_id(record.id) for record in records}) < len(records):
        raise ValueError("Two queries have the same published identifier")
    unsplit = [record.id for record in records if record.split not in SPLITS]
    if unsplit:
        raise ValueError(f"{len(unsplit)} queries have no split, e.g. {unsplit[0]}")
    counts = {}
    for split in SPLITS:
        rows = [to_row(record) for record in records if record.split == split]
        _write_rows(to / "queries" / f"{split}.jsonl", rows)
        counts[f"queries/{split}.jsonl"] = len(rows)
    ids = {record.id for record in records}
    for engine in engines:
        source = build / "runs" / f"{engine}.jsonl"
        results = {row["id"]: row for row in _read_rows(source)}
        missing = ids - set(results)
        if missing:
            raise ValueError(f"{engine} has no result for {len(missing)} queries")
        rows = sorted(
            (
                {"id": public_id(key), "documents": results[key]["documents"]}
                for key in ids
            ),
            key=lambda row: row["id"],
        )
        _write_rows(to / "runs" / f"{engine}.jsonl", rows)
        counts[f"runs/{engine}.jsonl"] = len(rows)
    return counts
