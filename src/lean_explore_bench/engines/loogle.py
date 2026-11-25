"""Loogle (loogle.lean-lang.org)."""

import urllib.parse
from dataclasses import dataclass

from lean_explore_bench.engines.base import Engine


@dataclass(frozen=True)
class Loogle(Engine):
    """Loogle, which searches by name fragment, constant and pattern.

    Loogle rejects input it cannot parse as one of its query forms; such a
    query returns no results rather than an error.
    """

    name: str = "loogle"
    interval_seconds: float = 2.0

    def search(self, query: str, limit: int) -> list[str]:
        """Search Loogle."""
        parameters = urllib.parse.urlencode({"q": query})
        reply = self._json(f"https://loogle.lean-lang.org/json?{parameters}")
        return [hit["name"] for hit in reply.get("hits", [])][:limit]
