"""The published form of the benchmark.

A build directory holds ``queries.jsonl`` with every working field. The
published dataset holds the same queries in a flat layout that dataset
viewers can read: ``queries/<split>.jsonl``, one row per query with a list of
answers, and ``runs/<engine>.jsonl``, the results of each engine.

:func:`load_queries` reads either layout, so the published dataset can be
scored directly.
"""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from lean_explore_bench.mix.assemble import SPLITS
from lean_explore_bench.mix.record import QueryRecord, read_records
from lean_explore_bench.mix.spec import BUCKET_OF_FORM, THREAD_BUCKET

_BLIND = {"question_before_answers": False}
"""Recorded blinding values that mean the writer had not seen the answers."""


def _saw_answers(record: QueryRecord) -> bool | None:
    """Whether the writer of a thread query had seen the thread's answers."""
    if record.source != "zulip":
        return None
    blinding = record.provenance.get("blinding")
    if blinding is None:
        return False
    return _BLIND.get(blinding, True)


def to_row(record: QueryRecord) -> dict[str, Any]:
    """Return the published row of one query.

    Answers are listed best grade first. ``pooled`` marks an answer that was
    found by grading engine results, not proposed when the query was made.
    """
    provenance = record.provenance
    pooled = set(provenance.get("pooled") or ())
    answers = [
        {"name": name, "grade": grade, "pooled": name in pooled}
        for name, grade in sorted(
            record.judgments.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    return {
        "id": record.id,
        "query": record.query,
        "bucket": BUCKET_OF_FORM.get(record.query_type, THREAD_BUCKET),
        "form": record.query_type,
        "variant": record.variant,
        "split": record.split,
        "source": record.source,
        "area": record.area,
        "target": record.target,
        "answers": answers,
        "group_id": record.group_id,
        "method": provenance.get("method", ""),
        "writer_model": provenance.get("writer_model"),
        "rewritten": "revised_from" in provenance,
        "judge_model": provenance.get("judge_model"),
        "pool_judge": provenance.get("pool_judge"),
        "thread_url": provenance.get("url"),
        "writer_saw_answers": _saw_answers(record),
    }


def from_row(row: dict[str, Any]) -> QueryRecord:
    """Build the working record of a published row."""
    provenance = {
        key: row[source]
        for key, source in (
            ("method", "method"),
            ("writer_model", "writer_model"),
            ("judge_model", "judge_model"),
            ("pool_judge", "pool_judge"),
            ("url", "thread_url"),
        )
        if row.get(source)
    }
    pooled = [answer["name"] for answer in row["answers"] if answer["pooled"]]
    if pooled:
        provenance["pooled"] = pooled
    return QueryRecord(
        id=row["id"],
        query=row["query"],
        query_type=row["form"],
        variant=row["variant"],
        source=row["source"],
        library="mathlib",
        area=row["area"],
        target=row["target"],
        judgments={answer["name"]: answer["grade"] for answer in row["answers"]},
        group_id=row["group_id"],
        provenance=provenance,
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
        ValueError: If a query has no split, or a run lacks a query.
    """
    records = sorted(read_records(build / "queries.jsonl"), key=lambda r: r.id)
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
        rows = [{"engine": engine, **results[key]} for key in sorted(ids)]
        _write_rows(to / "runs" / f"{engine}.jsonl", rows)
        counts[f"runs/{engine}.jsonl"] = len(rows)
    return counts
