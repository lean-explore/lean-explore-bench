"""Load and decrypt the benchmark query log into memory.

Decrypted queries are private. This module only ever returns them as an
in-memory DataFrame: it writes nothing to disk and never logs query text or
the key. Run it on the server that holds the database.
"""

import datetime
import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from cryptography.fernet import Fernet, InvalidToken

from lean_explore_bench.infra.settings import read_env_file
from lean_explore_bench.querylog.schema import QUERY_LOG_COLUMNS, TABLE_NAME

KEY_VARIABLE = "SEARCH_HISTORY_ENCRYPTION_KEY"
"""Name of the Fernet key variable in lean-explore-app's environment."""

DATABASE_PATH_VARIABLE = "LEB_QUERY_LOG_DB"
ENV_FILE_VARIABLE = "LEB_QUERY_LOG_ENV_FILE"

DEFAULT_APP_DIR = Path.home() / "lean-explore-app"
DEFAULT_DATABASE_PATH = DEFAULT_APP_DIR / "data" / "website_user_data.db"
DEFAULT_ENV_FILE = DEFAULT_APP_DIR / ".env"


@dataclass(frozen=True)
class LoadReport:
    """Counts describing a load, safe to display.

    Attributes:
        rows_read: Rows read from the table.
        rows_loaded: Rows decrypted successfully.
        rows_undecryptable: Rows whose token or JSON payload was invalid.
    """

    rows_read: int
    rows_loaded: int
    rows_undecryptable: int


def read_env_value(env_file: Path, name: str) -> str:
    """Read one variable from a dotenv-style file.

    Parsing (quotes, inline comments, ``export``) is shared with the rest of
    the project via :func:`lean_explore_bench.infra.settings.read_env_file`.

    Args:
        env_file: Path to a file of ``NAME=value`` lines.
        name: Variable to read.

    Returns:
        The value.

    Raises:
        KeyError: If the variable is missing or empty.
    """
    value = read_env_file(env_file).get(name)
    if not value:
        raise KeyError(f"{name} is not set in {env_file}")
    return value


def resolve_key(env_file: Path | None = None) -> str:
    """Find the Fernet key, preferring the environment over the env file.

    Args:
        env_file: Dotenv file to fall back on. Defaults to the
            ``LEB_QUERY_LOG_ENV_FILE`` variable, then lean-explore-app's
            ``.env``.

    Returns:
        The Fernet key.
    """
    key = os.environ.get(KEY_VARIABLE)
    if key:
        return key
    if env_file is None:
        env_file = Path(os.environ.get(ENV_FILE_VARIABLE, DEFAULT_ENV_FILE))
    return read_env_value(env_file, KEY_VARIABLE)


def resolve_database_path(database_path: Path | None = None) -> Path:
    """Return the query log database path.

    Args:
        database_path: Explicit path. Defaults to the ``LEB_QUERY_LOG_DB``
            variable, then lean-explore-app's website database.

    Returns:
        Path to the SQLite database.
    """
    if database_path is not None:
        return database_path
    return Path(os.environ.get(DATABASE_PATH_VARIABLE, DEFAULT_DATABASE_PATH))


def _decrypt_row(fernet: Fernet, token: str) -> tuple[str, tuple[str, ...]] | None:
    try:
        payload = json.loads(fernet.decrypt(token.encode("utf-8")).decode("utf-8"))
    except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError):
        return None
    query = payload.get("q") if isinstance(payload, dict) else None
    if not isinstance(query, str):
        return None
    packages = payload.get("pkg") or []
    return query, tuple(str(package) for package in packages)


def load_query_log(
    database_path: Path | None = None,
    key: str | None = None,
    since: datetime.date | None = None,
) -> tuple[pd.DataFrame, LoadReport]:
    """Read and decrypt the query log.

    The database is opened read-only, so this is safe to run against the live
    lean-explore-app database.

    Args:
        database_path: SQLite database; see :func:`resolve_database_path`.
        key: Fernet key; see :func:`resolve_key`.
        since: If set, only rows collected on or after this UTC day.

    Returns:
        A DataFrame with :data:`QUERY_LOG_COLUMNS`, sorted by ``row_id``, and a
        :class:`LoadReport`.
    """
    database_path = resolve_database_path(database_path)
    fernet = Fernet(key or resolve_key())
    sql = (
        f"SELECT id, encrypted_query_data, source, result_count, collected_on "
        f"FROM {TABLE_NAME}"
    )
    parameters: tuple[str, ...] = ()
    if since is not None:
        sql += " WHERE collected_on >= ?"
        parameters = (since.isoformat(),)
    sql += " ORDER BY id"

    uri = f"{database_path.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        rows = connection.execute(sql, parameters).fetchall()

    records = []
    for row_id, token, source, result_count, collected_on in rows:
        decrypted = _decrypt_row(fernet, token)
        if decrypted is None:
            continue
        query, packages = decrypted
        records.append(
            (
                row_id,
                query,
                packages,
                source,
                result_count,
                datetime.date.fromisoformat(collected_on),
            )
        )

    frame = pd.DataFrame.from_records(records, columns=list(QUERY_LOG_COLUMNS))
    report = LoadReport(
        rows_read=len(rows),
        rows_loaded=len(records),
        rows_undecryptable=len(rows) - len(records),
    )
    return frame, report
