"""Shape of the LeanExplore benchmark query log.

Mirrors the ``benchmark_queries`` table written by lean-explore-app
(``app/backend/models/benchmark.py``). Each row is one search, stored
without any user, session or network identifier. The query text and package
filters are a Fernet-encrypted JSON object ``{"q": str, "pkg": list[str]}``.
"""

from typing import Literal

Source = Literal["web", "web_account", "api", "mcp"]
"""Where a query came from, as recorded by lean-explore-app."""

SOURCES: tuple[Source, ...] = ("web", "web_account", "api", "mcp")

TABLE_NAME = "benchmark_queries"

QUERY_LOG_COLUMNS: tuple[str, ...] = (
    "row_id",
    "query",
    "packages",
    "source",
    "result_count",
    "collected_on",
)
"""Columns of a decrypted query log DataFrame.

- ``row_id``: primary key of the log row.
- ``query``: the search text.
- ``packages``: tuple of package filters (empty when none were applied).
- ``source``: one of :data:`SOURCES`.
- ``result_count``: number of results returned, or ``None``.
- ``collected_on``: UTC day of the search (``datetime.date``).
"""
