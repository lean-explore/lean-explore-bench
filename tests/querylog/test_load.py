import datetime
import json
import sqlite3
from pathlib import Path

import pandas as pd
import pytest
from cryptography.fernet import Fernet

from lean_explore_bench.querylog import load
from lean_explore_bench.querylog.load import (
    load_query_log,
    read_env_value,
    resolve_database_path,
    resolve_key,
)
from lean_explore_bench.querylog.schema import QUERY_LOG_COLUMNS, TABLE_NAME


def test_round_trip_through_encrypted_database(
    encrypted_log: Path, shaped_log: pd.DataFrame
) -> None:
    loaded, report = load_query_log(encrypted_log)
    assert list(loaded.columns) == list(QUERY_LOG_COLUMNS)
    assert report.rows_loaded == report.rows_read == len(shaped_log)
    assert loaded["query"].tolist() == shaped_log["query"].tolist()


def test_since_filters_by_day(encrypted_log: Path, day: datetime.date) -> None:
    later = day + datetime.timedelta(days=1)
    loaded, _ = load_query_log(encrypted_log, since=later)
    assert set(loaded["collected_on"]) == {later}


def test_wrong_key_rows_are_counted_not_raised(
    encrypted_log: Path, shaped_log: pd.DataFrame
) -> None:
    loaded, report = load_query_log(encrypted_log, key=Fernet.generate_key().decode())
    assert loaded.empty
    assert report.rows_undecryptable == len(shaped_log)


def test_rows_with_bad_payloads_are_skipped(tmp_path: Path) -> None:
    key = Fernet.generate_key()
    fernet = Fernet(key)
    tokens = [
        fernet.encrypt(b"not json"),
        fernet.encrypt(json.dumps(["a list"]).encode()),
        fernet.encrypt(json.dumps({"q": 7}).encode()),
        fernet.encrypt(json.dumps({"q": "kept", "pkg": None}).encode()),
    ]
    database = tmp_path / "log.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            f"CREATE TABLE {TABLE_NAME} (id INTEGER PRIMARY KEY, "
            "encrypted_query_data TEXT, source TEXT, result_count INTEGER, "
            "collected_on DATE)"
        )
        connection.executemany(
            f"INSERT INTO {TABLE_NAME} VALUES (?, ?, 'api', 1, '2026-09-01')",
            [(i, token.decode()) for i, token in enumerate(tokens)],
        )
    loaded, report = load_query_log(database, key=key.decode())
    assert loaded["query"].tolist() == ["kept"]
    assert loaded["packages"].tolist() == [()]
    assert report.rows_undecryptable == 3


def test_read_env_value(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "# comment\nOTHER=1\nexport NAME='secret'\nEMPTY=\n", encoding="utf-8"
    )
    assert read_env_value(env, "NAME") == "secret"
    for missing in ("MISSING", "EMPTY"):
        with pytest.raises(KeyError):
            read_env_value(env, missing)


def test_resolve_key_prefers_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = tmp_path / ".env"
    env.write_text("SEARCH_HISTORY_ENCRYPTION_KEY=from-file\n", encoding="utf-8")
    monkeypatch.delenv("SEARCH_HISTORY_ENCRYPTION_KEY", raising=False)
    assert resolve_key(env) == "from-file"
    monkeypatch.setenv("LEB_QUERY_LOG_ENV_FILE", str(env))
    assert resolve_key() == "from-file"
    monkeypatch.setenv("SEARCH_HISTORY_ENCRYPTION_KEY", "from-env")
    assert resolve_key(env) == "from-env"


def test_resolve_database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    explicit = tmp_path / "explicit.db"
    assert resolve_database_path(explicit) == explicit
    monkeypatch.setenv("LEB_QUERY_LOG_DB", str(tmp_path / "env.db"))
    assert resolve_database_path() == tmp_path / "env.db"
    monkeypatch.delenv("LEB_QUERY_LOG_DB")
    assert resolve_database_path() == load.DEFAULT_DATABASE_PATH


def test_read_env_value_ignores_inline_comments(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text('SEARCH_HISTORY_ENCRYPTION_KEY="k#1" # note\n', encoding="utf-8")
    assert read_env_value(env, "SEARCH_HISTORY_ENCRYPTION_KEY") == "k#1"
