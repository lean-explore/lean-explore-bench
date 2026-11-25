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
from lean_explore_bench.mix.corpus import Corpus, load_corpus
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


Row = tuple[str, str, str | None, str, str | None]


def _theorem_row(name: str, module: str) -> Row:
    short = name.rsplit(".", 1)[-1]
    source = (
        f"/-- Addition commutes ({short}). -/\n"
        f"theorem {short} (a b : Nat) : a + b = b + a := by\n  omega\n"
    )
    return (name, module, f"Addition commutes ({short}).", source, f"About {short}.")


def _corpus_rows() -> list[Row]:
    rows: list[Row] = []
    for area in ("Algebra", "Topology"):
        rows += [
            _theorem_row(f"Demo.{area}.add_comm_{i}", f"Mathlib.{area}.Basic")
            for i in range(12)
        ]
    rows += [
        _theorem_row(f"Cslib.Demo.step_comm_{i}", "Cslib.Foundations.Basic")
        for i in range(8)
    ]
    rows += [
        (
            "Demo.Algebra.double",
            "Mathlib.Algebra.Basic",
            None,
            "def double (n : Nat) : Nat := n + n -- doubles a natural number\n",
            None,
        ),
        (
            "Demo.Algebra.Pair",
            "Mathlib.Algebra.Basic",
            None,
            "structure Pair where\n  left : Nat\n  right : Nat\n  deriving Repr\n",
            None,
        ),
        # Generated: the source is the parent structure.
        (
            "Demo.Algebra.Pair.left",
            "Mathlib.Algebra.Basic",
            None,
            "structure Pair where\n  left : Nat\n  right : Nat\n  deriving Repr\n",
            None,
        ),
        _theorem_row("Demo.Tactic.helper_lemma", "Mathlib.Tactic.Helper"),
        _theorem_row("Lean.Meta.internal_lemma", "Lean.Meta.Basic"),
        (
            "Demo.Algebra.old_lemma",
            "Mathlib.Algebra.Basic",
            None,
            '@[deprecated (since := "2026-01-01")]\n'
            "theorem old_lemma (a : Nat) : a + 0 = a := by simp\n",
            None,
        ),
        ("Demo.Algebra.tiny", "Mathlib.Algebra.Basic", None, "def tiny := 1\n", None),
        (
            "Demo.Algebra.instAdd",
            "Mathlib.Algebra.Basic",
            None,
            "instance : Add Pair := ⟨fun a b => ⟨a.left + b.left, a.right⟩⟩\n",
            None,
        ),
    ]
    return rows


def _write_corpus(path: Path, rows: list[Row]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE declarations (name TEXT, module TEXT, docstring TEXT, "
        "source_text TEXT, informalization TEXT)"
    )
    connection.executemany("INSERT INTO declarations VALUES (?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return path


@pytest.fixture
def corpus_path(tmp_path: Path) -> Path:
    """A tiny LeanExplore corpus snapshot: 40 declarations, 34 eligible."""
    return _write_corpus(tmp_path / "snapshot-1" / "lean_explore.db", _corpus_rows())


@pytest.fixture
def corpus(corpus_path: Path) -> Corpus:
    """The tiny corpus, loaded."""
    return load_corpus(corpus_path)
