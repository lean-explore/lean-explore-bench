"""Assemble accepted queries into the mix, split it, and export it.

``queries.jsonl`` holds every record with its provenance.
"""

import hashlib
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from lean_explore_bench.builder.sample import Target
from lean_explore_bench.record import SPLITS, QueryRecord
from lean_explore_bench.spec import MixSpec


def _cells(targets: Iterable[Target]) -> dict[tuple[str, str], list[Target]]:
    """Group targets by (bucket, library), each cell in sampling order."""
    cells: dict[tuple[str, str], list[Target]] = defaultdict(list)
    for target in targets:
        cells[(target.query_type, target.declaration.library)].append(target)
    for members in cells.values():
        members.sort(key=lambda target: target.order)
    return cells


def _pool(
    done: dict[str, dict[str, Any]], allowed: Callable[[str], bool]
) -> dict[tuple[str, str], list[QueryRecord]]:
    """Accepted written queries of the journal, by (bucket, library).

    The journal can hold queries for targets that the current sample does
    not draw, because the shape of the mix changed since they were written.
    They are still valid, so they count towards a cell before anything new
    is written for it.
    """
    pool: dict[tuple[str, str], list[QueryRecord]] = defaultdict(list)
    for entry in done.values():
        if entry["accepted"]:
            record = QueryRecord.from_json(entry["record"])
            if record.source == "declaration" and allowed(record.target):
                pool[(record.query_type, record.library)].append(record)
    return pool


def _always(_name: str) -> bool:
    return True


def needed(
    targets: Iterable[Target],
    done: dict[str, dict[str, Any]],
    spec: MixSpec,
    allowed: Callable[[str], bool] = _always,
) -> list[Target]:
    """Return the targets that still need a query written.

    Each cell is walked in sampling order. Reserves are used only as far as
    needed to replace rejected targets, so no query is written in vain.

    Args:
        targets: Targets of the buckets written by a language model.
        done: Journal entries keyed by target identifier.
        spec: The mix specification.
        allowed: Whether a declaration may be a target; others are skipped.
    """
    pool = _pool(done, allowed)
    pending: list[Target] = []
    for (query_type, library), members in _cells(targets).items():
        remaining = spec.count(query_type, library) - len(pool[(query_type, library)])
        for target in members:
            if remaining <= 0:
                break
            if target.id not in done and allowed(target.declaration.name):
                pending.append(target)
                remaining -= 1
    return pending


def select(
    targets: Iterable[Target],
    done: dict[str, dict[str, Any]],
    spec: MixSpec,
    allowed: Callable[[str], bool] = _always,
) -> list[QueryRecord]:
    """Pick each cell's quota of accepted queries, in sampling order.

    Queries for targets outside the current sample come after those inside
    it. A small library can run out of targets for a form. The queries a
    bucket then lacks are taken from the accepted queries its other
    libraries hold beyond their quota, largest library first, so that the
    bucket still reaches its size.
    """
    pool = _pool(done, allowed)
    chosen: list[QueryRecord] = []
    spare: dict[str, list[QueryRecord]] = defaultdict(list)
    lacking: dict[str, int] = defaultdict(int)
    cells = _cells(targets)
    order = sorted(cells, key=lambda cell: -spec.library_counts[cell[1]])
    for query_type, library in order:
        position = {
            target.id: index
            for index, target in enumerate(cells[(query_type, library)])
        }
        accepted = sorted(
            pool[(query_type, library)],
            key=lambda record: (position.get(record.id, len(position)), record.id),
        )
        quota = spec.count(query_type, library)
        chosen.extend(accepted[:quota])
        spare[query_type].extend(accepted[quota:])
        lacking[query_type] += max(0, quota - len(accepted))
    for query_type, missing in lacking.items():
        chosen.extend(spare[query_type][:missing])
    return chosen


def assign_splits(records: Iterable[QueryRecord], spec: MixSpec) -> list[QueryRecord]:
    """Place every record in the development or the test split.

    Groups, not queries, are assigned, so that related queries never
    straddle the split. Within each bucket the groups are ordered by a
    seeded hash and taken for development until it holds
    ``development_share`` of the bucket's queries. Both splits therefore
    keep the shape of the mix, and a bucket of 200 gives exactly 40.
    """
    by_bucket: dict[str, dict[str, list[QueryRecord]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for record in records:
        by_bucket[record.query_type][record.group_id].append(record)
    assigned: list[QueryRecord] = []
    for groups in by_bucket.values():
        ordered = sorted(
            groups,
            key=lambda group: hashlib.sha256(f"{spec.seed}:{group}".encode()).digest(),
        )
        size = sum(len(members) for members in groups.values())
        room = round(size * spec.development_share)
        for group in ordered:
            members = groups[group]
            development = len(members) <= room
            room -= len(members) if development else 0
            assigned.extend(
                QueryRecord.from_json(
                    {**member.to_json(), "split": SPLITS[0 if development else 1]}
                )
                for member in members
            )
    return sorted(assigned, key=lambda record: record.id)


def summary_table(records: Iterable[QueryRecord]) -> str:
    """Render query counts by bucket and library as a Markdown table."""
    counts = Counter((record.query_type, record.library) for record in records)
    buckets = sorted({bucket for bucket, _ in counts})
    libraries = sorted({library for _, library in counts})
    header = "| Query type | " + " | ".join(libraries) + " | Total |"
    rule = "| --- | " + " | ".join("---:" for _ in libraries) + " | ---: |"
    rows = [header, rule]
    for bucket in buckets:
        cells = [counts[(bucket, library)] for library in libraries]
        rows.append(
            f"| {bucket} | " + " | ".join(map(str, cells)) + f" | {sum(cells)} |"
        )
    totals = [sum(counts[(b, library)] for b in buckets) for library in libraries]
    rows.append("| Total | " + " | ".join(map(str, totals)) + f" | {sum(totals)} |")
    return "\n".join(rows) + "\n"
