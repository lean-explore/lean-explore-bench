"""The search engines the benchmark can run, one module per engine.

Three are hosted services: LeanExplore, LeanSearch and Lean Finder. They
index their own snapshots of Mathlib, which are not pinned and change
over time. The fourth, BM25 in :mod:`lean_explore_bench.engines.bm25`, is a
local baseline with no learned component; it needs a corpus snapshot and the
``bm25`` extra, so it is imported only when used.

To add an engine, write a module with a subclass of :class:`Engine` and add
it to :data:`ENGINES`.
"""

from collections.abc import Callable

from lean_explore_bench.engines.base import (
    TIMEOUT_SECONDS,
    USER_AGENT,
    Engine,
    Fetch,
    http_fetch,
)
from lean_explore_bench.engines.leanexplore import LeanExplore
from lean_explore_bench.engines.leanfinder import LeanFinder
from lean_explore_bench.engines.leansearch import LeanSearch
from lean_explore_bench.engines.runner import read_results, run

ENGINES: dict[str, Callable[[], Engine]] = {
    "leanexplore": LeanExplore,
    "leansearch": LeanSearch,
    "leanfinder": LeanFinder,
}
"""The hosted engines, by name."""

LOCAL_ENGINES = ("bm25",)
"""Engines that run locally on a corpus snapshot."""

__all__ = [
    "ENGINES",
    "LOCAL_ENGINES",
    "TIMEOUT_SECONDS",
    "USER_AGENT",
    "Engine",
    "Fetch",
    "LeanExplore",
    "LeanFinder",
    "LeanSearch",
    "http_fetch",
    "read_results",
    "run",
]
