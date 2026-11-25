"""LeanSearch (leansearch.net)."""

from dataclasses import dataclass

from lean_explore_bench.engines.base import Engine


@dataclass(frozen=True)
class LeanSearch(Engine):
    """LeanSearch (leansearch.net)."""

    name: str = "leansearch"
    interval_seconds: float = 2.0

    def search(self, query: str, limit: int) -> list[str]:
        """Search LeanSearch."""
        reply = self._json(
            "https://leansearch.net/search",
            {"query": [query], "num_results": str(limit)},
        )
        hits = reply[0] if reply else []
        return [".".join(hit["result"]["name"]) for hit in hits][:limit]
