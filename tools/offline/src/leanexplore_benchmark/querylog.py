"""Load the source-keyed query export; never print or persist raw queries."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SOURCES = ("web", "web_account", "api", "mcp")


@dataclass(frozen=True)
class Query:
    """One request, with export position rather than a person or session ID."""

    position: int
    source: str
    text: str
    packages: tuple[str, ...]
    result_count: int | None
    day: dt.date


@dataclass(frozen=True)
class Export:
    """Selected requests and reproducibility metadata."""

    rows: tuple[Query, ...]
    sha256: str
    rows_read: int


def load_export(path: Path, since: dt.date | None = None) -> Export:
    """Validate every record, including records excluded by the date filter.

    Fail rather than silently dropping malformed data. Errors identify record
    positions only. Missing sources are allowed; unknown sources are refused.
    """
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Invalid query-export JSON") from None
    if not isinstance(payload, dict) or set(payload) - set(SOURCES):
        raise ValueError("Expected an object keyed only by known sources")
    records = []
    rows_read = 0
    for source in SOURCES:
        rows = payload.get(source, [])
        if not isinstance(rows, list):
            raise ValueError(f"Expected a list for source {source}")
        for position, row in enumerate(rows, 1):
            rows_read += 1
            try:
                if not isinstance(row, dict):
                    raise ValueError
                query = row["query"]
                packages = row["package_filters"]
                count = row["result_count"]
                day_text = row["collected_on"]
                if not isinstance(query, str):
                    raise ValueError
                if not isinstance(packages, list) or any(
                    not isinstance(p, str) or not p for p in packages
                ):
                    raise ValueError
                if count is not None and (type(count) is not int or count < 0):
                    raise ValueError
                if not isinstance(day_text, str):
                    raise ValueError
                day = dt.date.fromisoformat(day_text)
                if day.isoformat() != day_text:
                    raise ValueError
            except (KeyError, TypeError, ValueError):
                raise ValueError(
                    f"Invalid record at source {source}, position {position}"
                ) from None
            if since is None or day >= since:
                records.append(
                    Query(rows_read, source, query, tuple(packages), count, day)
                )
    return Export(tuple(records), hashlib.sha256(raw).hexdigest(), rows_read)


def normalize(text: str) -> str:
    """Use conservative NFC and whitespace normalization; preserve Lean case.

    Do not collapse ASCII operators or paraphrases here: query semantics may
    change. Near-duplicate sensitivity belongs to a separate validation step.
    """
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def request_key(row: Query) -> tuple[str, tuple[str, ...]]:
    """Identity of a query plus unordered package filters, without its source."""
    return normalize(row.text), tuple(sorted(set(row.packages)))
