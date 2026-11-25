"""Send benchmark queries to hosted Lean search engines.

Every engine is reduced to one function: a query goes in, a ranked list of
declaration names comes out. Results are appended to a journal as they
arrive, so a run can be interrupted and resumed, and requests are spaced to
respect each service's rate limit.

Hosted engines index their own snapshot of the libraries, which is not
pinned and may differ from the benchmark corpus. Their scores are therefore
reported separately from runs on the pinned corpus.
"""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lean_explore_bench.record import QueryRecord

USER_AGENT = "lean-search-benchmark"
TIMEOUT_SECONDS = 60

Fetch = Callable[[urllib.request.Request], bytes]


def http_fetch(request: urllib.request.Request) -> bytes:
    """Perform an HTTP request and return the response body."""
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body: bytes = response.read()
    return body


@dataclass(frozen=True)
class Engine:
    """A hosted search engine.

    Attributes:
        name: Short name, used for file names.
        interval_seconds: Minimum time between two requests.
        fetch: Function that performs an HTTP request.
    """

    name: str = ""
    interval_seconds: float = 1.0
    fetch: Fetch = http_fetch

    def search(self, query: str, limit: int) -> list[str]:
        """Return the names of the top ``limit`` declarations for ``query``."""
        raise NotImplementedError

    def _json(self, url: str, payload: dict[str, Any] | None = None) -> Any:
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        request = urllib.request.Request(url, data=data, headers=headers)
        return json.loads(self.fetch(request))


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


ENGINES: dict[str, Callable[[], Engine]] = {
    "leanexplore": LeanExplore,
    "leansearch": LeanSearch,
    "loogle": Loogle,
    "leanfinder": LeanFinder,
}


def read_results(path: Path) -> dict[str, dict[str, Any]]:
    """Read a run journal; the last entry for a query wins."""
    if not path.exists():
        return {}
    entries = (
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    return {entry["id"]: entry for entry in entries}


def run(
    engine: Engine,
    records: Iterable[QueryRecord],
    journal: Path,
    limit: int = 10,
    pause: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, dict[str, Any]]:
    """Send every query not yet answered to ``engine``.

    A request that raises is recorded with status ``error`` and no
    documents, and is retried on the next run.

    Args:
        engine: The engine.
        records: The queries.
        journal: JSON Lines file that receives one entry per query.
        limit: Results requested per query.
        pause: Sleep function, replaceable in tests.
        clock: Monotonic clock, replaceable in tests.

    Returns:
        The result of every query: status, ranked names and latency.
    """
    results = read_results(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as file:
        for record in records:
            if results.get(record.id, {}).get("status") == "ok":
                continue
            started = clock()
            entry: dict[str, Any] = {"id": record.id, "limit": limit}
            try:
                documents = engine.search(record.query, limit)
                entry |= {"status": "ok", "documents": documents}
            except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
                entry |= {"status": "error", "documents": [], "error": repr(error)}
            entry["latency_ms"] = round((clock() - started) * 1000, 1)
            results[record.id] = entry
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            file.flush()
            pause(engine.interval_seconds)
    return results
