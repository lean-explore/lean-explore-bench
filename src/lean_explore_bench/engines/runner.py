"""Run an engine on the benchmark queries and keep its results.

Results are appended to a journal as they arrive, so a run can be interrupted
and resumed, and requests are spaced to respect each service's rate limit.
"""

import json
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from lean_explore_bench.engines.base import Engine
from lean_explore_bench.record import QueryRecord


def read_results(path: Path) -> dict[str, dict[str, Any]]:
    """Read a run journal; the last entry for a query wins."""
    if not path.exists():
        return {}
    entries = (
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    return {entry["id"]: entry for entry in entries}


def run(
    engine: Engine,
    records: Iterable[QueryRecord],
    journal: Path,
    limit: int = 10,
    pause: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, dict[str, Any]]:
    """Send every query not yet answered to ``engine``.

    A request that raises is recorded with status ``error`` and no
    documents, and is retried on the next run.

    Args:
        engine: The engine.
        records: The queries.
        journal: JSON Lines file that receives one entry per query.
        limit: Results requested per query.
        pause: Sleep function, replaceable in tests.
        clock: Monotonic clock, replaceable in tests.

    Returns:
        The result of every query: status, ranked names and latency.
    """
    results = read_results(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as file:
        for record in records:
            if results.get(record.id, {}).get("status") == "ok":
                continue
            started = clock()
            entry: dict[str, Any] = {"id": record.id, "limit": limit}
            try:
                documents = engine.search(record.query, limit)
                entry |= {"status": "ok", "documents": documents}
            except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
                entry |= {"status": "error", "documents": [], "error": repr(error)}
            entry["latency_ms"] = round((clock() - started) * 1000, 1)
            results[record.id] = entry
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            file.flush()
            pause(engine.interval_seconds)
    return results
