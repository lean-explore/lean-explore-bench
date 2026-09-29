"""Shared fixtures. Test data is small, inline and built from placeholders."""

import datetime
import json
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest
from cryptography.fernet import Fernet

from lean_explore_bench.analysis.stats import PreparedLog, prepare
from lean_explore_bench.querylog.schema import QUERY_LOG_COLUMNS, TABLE_NAME

DAY = datetime.date(2026, 9, 1)

LogRow = tuple[str, str, datetime.date, int]
MakeLog = Callable[[list[LogRow]], pd.DataFrame]
WriteLog = Callable[[pd.DataFrame, Path, str], None]


def _make_log(rows: list[LogRow]) -> pd.DataFrame:
    frame = pd.DataFrame(
        rows, columns=["query", "source", "collected_on", "result_count"]
    )
    frame["packages"] = [()] * len(frame)
    frame.insert(0, "row_id", range(1, len(frame) + 1))
    return frame[list(QUERY_LOG_COLUMNS)]


def _write_encrypted_log(frame: pd.DataFrame, path: Path, key: str) -> None:
    fernet = Fernet(key.encode())
    rows = [
        (
            row_id,
            fernet.encrypt(json.dumps({"q": q, "pkg": list(pkg)}).encode()).decode(),
            source,
            results,
            day.isoformat(),
        )
        for row_id, q, pkg, source, results, day in zip(
            *(frame[column].tolist() for column in QUERY_LOG_COLUMNS)
        )
    ]
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"CREATE TABLE {TABLE_NAME} (id INTEGER PRIMARY KEY, "
            "encrypted_query_data TEXT NOT NULL, source VARCHAR(16) NOT NULL, "
            "result_count INTEGER, collected_on DATE NOT NULL)"
        )
        connection.executemany(f"INSERT INTO {TABLE_NAME} VALUES (?, ?, ?, ?, ?)", rows)


def _shaped_queries(n: int) -> list[str]:
    names = [f"Alpha{i}.beta_{i}" for i in range(n)]
    keywords = [f"term{i} word{i} thing{i} item{i} piece{i}" for i in range(n)]
    prose = [
        f"is there a result that the term{i} of a word{i} is in the set"
        for i in range(n)
    ]
    return names + keywords + prose


@pytest.fixture(scope="session")
def day() -> datetime.date:
    """The first day of every test log."""
    return DAY


@pytest.fixture(scope="session")
def make_log() -> MakeLog:
    """Build a log from (query, source, day, result count) rows."""
    return _make_log


@pytest.fixture(scope="session")
def write_encrypted_log() -> WriteLog:
    """Write a log in lean-explore-app's encrypted table format."""
    return _write_encrypted_log


@pytest.fixture(scope="session")
def shaped_log() -> pd.DataFrame:
    """180 searches over 150 distinct placeholder queries in three shapes.

    Names (``Alpha1.beta_1``), word runs and sentences, 50 of each; the first
    30 are searched again the next day over MCP. Only structure matters.
    """
    queries = _shaped_queries(50)
    rows = [(q, "api", DAY, 8) for q in queries]
    rows += [(q, "mcp", DAY + datetime.timedelta(days=1), 3) for q in queries[:30]]
    return _make_log(rows)


@pytest.fixture(scope="session")
def prepared(shaped_log: pd.DataFrame) -> PreparedLog:
    """The shaped log, prepared.

    Placeholders such as ``term1`` and ``term11`` are near-duplicates by
    construction, so only exact duplicates are merged.
    """
    return prepare(shaped_log, threshold=1.0)


@pytest.fixture
def encrypted_log(
    tmp_path: Path, shaped_log: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """The shaped log in an encrypted database, with its key in the env."""
    key = Fernet.generate_key().decode()
    database = tmp_path / "log.db"
    _write_encrypted_log(shaped_log, database, key)
    monkeypatch.setenv("SEARCH_HISTORY_ENCRYPTION_KEY", key)
    return database
