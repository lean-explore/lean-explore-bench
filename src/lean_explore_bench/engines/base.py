"""What every search engine has in common.

An engine is reduced to one function: a query goes in, a ranked list of
declaration names comes out.
"""

import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
    """A search engine.

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
