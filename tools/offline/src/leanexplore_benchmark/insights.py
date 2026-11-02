"""Workload analysis. Raw text and per-query keys stay in memory."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from leanexplore_benchmark.profile import release, rounded, surface
from leanexplore_benchmark.querylog import Query, request_key


def _safe_count(n: int) -> int | None:
    return rounded(n) if n >= 10 else None


def _partition(counts: Counter[str]) -> dict[str, int | None]:
    """Apply primary and complementary small-cell suppression."""
    cells = release(Counter({("all", k): v for k, v in counts.items() if v > 0}), 10)
    visible = {
        str(c["category"]): c["count"] if isinstance(c["count"], int) else None
        for c in cells
    }
    return {**{k: 0 for k, v in counts.items() if v == 0}, **visible}


def _length(text: str) -> str:
    n = len(text.split())
    return "0-2" if n <= 2 else "3-8" if n <= 8 else "9-16" if n <= 16 else "17+"


def _group(rows: tuple[Query, ...]) -> dict[str, Any]:
    grouped: dict[tuple[str, tuple[str, ...]], list[Query]] = defaultdict(list)
    for row in rows:
        grouped[request_key(row)].append(row)
    unique = tuple(group[0] for group in grouped.values())
    frequency: Counter[str] = Counter()
    recurrence: Counter[str] = Counter()
    variability: Counter[str] = Counter()
    for group in grouped.values():
        frequency[
            "once" if len(group) == 1 else "2-5" if len(group) <= 5 else "6+"
        ] += len(group)
        recurrence[
            "one_day" if len({r.day for r in group}) == 1 else "multiple_days"
        ] += 1
        if len(group) >= 2:
            counts = {r.result_count for r in group if r.result_count is not None}
            label = (
                "missing"
                if any(r.result_count is None for r in group)
                else "same_count"
                if len(counts) == 1
                else "different_counts"
            )
            variability[label] += 1
    views = {}
    for name, selected in (("requests", rows), ("distinct", unique)):
        views[name] = {
            "surface": _partition(Counter(surface(r.text) for r in selected)),
            "length": _partition(Counter(_length(r.text) for r in selected)),
            "filters": _partition(
                Counter(
                    "with_filter" if r.packages else "without_filter" for r in selected
                )
            ),
        }
    repeat_counts = _partition(
        Counter({"distinct": len(unique), "extra_occurrences": len(rows) - len(unique)})
    )
    return {
        "requests": _safe_count(len(rows)),
        "repeat_accounting": repeat_counts,
        "frequency_events": _partition(frequency),
        "recurrence_distinct": _partition(recurrence),
        "repeated_result_counts": _partition(variability),
        "views": views,
    }


def analyze(rows: tuple[Query, ...]) -> dict[str, Any]:
    """Compare windows, channels, repetitions and observable query forms."""
    if not rows:
        raise ValueError("No queries selected")
    first = min(r.day for r in rows)
    windows = {
        "full": rows,
        "first_day": tuple(r for r in rows if r.day == first),
        "later": tuple(r for r in rows if r.day > first),
    }
    result: dict[str, Any] = {
        "first_day": first.isoformat(),
        "last_day": max(r.day for r in rows).isoformat(),
        "windows": {},
        "daily": _partition(Counter(r.day.isoformat() for r in rows)),
    }
    for name, selected in windows.items():
        channels = {}
        for source in ("api", "web", "mcp", "web_account"):
            subset = tuple(r for r in selected if r.source == source)
            if len(subset) >= 100:
                channels[source] = _group(subset)
        result["windows"][name] = {
            "all": _group(selected) if selected else None,
            "channels": channels,
            "channel_counts": _partition(Counter(r.source for r in selected)),
        }
    return result
