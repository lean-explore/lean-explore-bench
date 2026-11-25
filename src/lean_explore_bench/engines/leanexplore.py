"""LeanExplore (leanexplore.com)."""

import urllib.parse
from dataclasses import dataclass

from lean_explore_bench.engines.base import Engine


@dataclass(frozen=True)
class LeanExplore(Engine):
    """LeanExplore's public API (30 searches per minute per address)."""

    name: str = "leanexplore"
    interval_seconds: float = 2.1

    def search(self, query: str, limit: int) -> list[str]:
        """Search LeanExplore."""
        parameters = urllib.parse.urlencode({"q": query, "limit": limit})
        reply = self._json(f"https://www.leanexplore.com/api/v2/search?{parameters}")
        return [result["name"] for result in reply["results"]][:limit]
