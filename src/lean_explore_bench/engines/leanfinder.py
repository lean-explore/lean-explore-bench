"""Lean Finder."""

import re
import urllib.parse
from dataclasses import dataclass

from lean_explore_bench.engines.base import Engine


@dataclass(frozen=True)
class LeanFinder(Engine):
    """Lean Finder's hosted inference endpoint."""

    name: str = "leanfinder"
    interval_seconds: float = 3.0

    _pattern = re.compile(r"pattern=(.*?)#doc")

    def search(self, query: str, limit: int) -> list[str]:
        """Search Lean Finder."""
        reply = self._json(
            "https://bxrituxuhpc70w8w.us-east-1.aws.endpoints.huggingface.cloud",
            {"inputs": query, "top_k": limit},
        )
        names = []
        for result in reply["results"]:
            match = self._pattern.search(result.get("url", ""))
            if match is not None:
                names.append(urllib.parse.unquote(match.group(1)))
        return names[:limit]
