import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from lean_explore_bench import engines
from lean_explore_bench.record import QueryRecord


def _record(identifier: str, query: str = "a query") -> QueryRecord:
    return QueryRecord(
        id=identifier,
        query=query,
        query_type="informal",
        variant="statement",
        source="declaration",
        library="mathlib",
        area="Algebra",
        target="T",
        judgments={"T": 3},
        group_id="T",
    )


def _body(request: urllib.request.Request) -> bytes:
    assert isinstance(request.data, bytes)
    return request.data


class Recorder:
    """Returns a canned body and records every request."""

    def __init__(self, body: Any) -> None:
        self.body = body
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request) -> bytes:
        self.requests.append(request)
        return json.dumps(self.body).encode()


def test_leanexplore_reads_result_names() -> None:
    fetch = Recorder({"results": [{"name": "A.b"}, {"name": "C.d"}, {"name": "E"}]})
    assert engines.LeanExplore(fetch=fetch).search("sum of evens", 2) == ["A.b", "C.d"]
    request = fetch.requests[0]
    assert request.full_url == (
        "https://www.leanexplore.com/api/v2/search?q=sum+of+evens&limit=2"
    )
    assert request.get_method() == "GET"
    assert request.get_header("User-agent") == engines.USER_AGENT


def test_leansearch_posts_the_query_and_joins_name_parts() -> None:
    fetch = Recorder([[{"result": {"name": ["Nat", "add_comm"]}}]])
    assert engines.LeanSearch(fetch=fetch).search("q", 5) == ["Nat.add_comm"]
    request = fetch.requests[0]
    assert request.get_method() == "POST"
    assert json.loads(_body(request)) == {"query": ["q"], "num_results": "5"}
    assert engines.LeanSearch(fetch=Recorder([])).search("q", 5) == []


def test_loogle_returns_nothing_for_unparsable_input() -> None:
    fetch = Recorder({"hits": [{"name": "Nat.add_comm"}, {"name": "X"}]})
    assert engines.Loogle(fetch=fetch).search("Nat.add_comm", 1) == ["Nat.add_comm"]
    assert "q=Nat.add_comm" in fetch.requests[0].full_url
    assert engines.Loogle(fetch=Recorder({"error": "parse"})).search("a b", 5) == []


def test_leanfinder_extracts_names_from_documentation_links() -> None:
    base = "https://leanprover-community.github.io/mathlib4_docs/find/?pattern="
    fetch = Recorder(
        {
            "results": [
                {"url": f"{base}Nat.add_comm#doc"},
                {"url": "https://example.org/other"},
                {"url": f"{base}Stream%27.map#doc"},
                {},
            ]
        }
    )
    found = engines.LeanFinder(fetch=fetch).search("q", 5)
    assert found == ["Nat.add_comm", "Stream'.map"]
    assert json.loads(_body(fetch.requests[0])) == {"inputs": "q", "top_k": 5}


def test_registry_and_base_engine() -> None:
    assert set(engines.ENGINES) == {"leanexplore", "leansearch", "loogle", "leanfinder"}
    assert all(make().name == name for name, make in engines.ENGINES.items())
    with pytest.raises(NotImplementedError):
        engines.Engine().search("q", 1)


def test_http_fetch_reads_the_body(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return b"{}"

    seen: dict[str, Any] = {}

    def urlopen(request: urllib.request.Request, timeout: float) -> Response:
        seen["timeout"] = timeout
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    assert engines.http_fetch(urllib.request.Request("https://example.org")) == b"{}"
    assert seen["timeout"] == engines.TIMEOUT_SECONDS


def test_run_journals_resumes_and_retries_failures(tmp_path: Path) -> None:
    class Flaky(engines.Engine):
        def search(self, query: str, limit: int) -> list[str]:
            if query == "bad" and not healthy:
                raise urllib.error.URLError("down")
            return [f"hit for {query}"][:limit]

    journal = tmp_path / "runs" / "flaky.jsonl"
    records = [_record("q1", "good"), _record("q2", "bad")]
    pauses: list[float] = []
    ticks = iter(range(100))
    healthy = False
    assert engines.read_results(journal) == {}
    results = engines.run(
        Flaky(name="flaky", interval_seconds=0.5),
        records,
        journal,
        limit=3,
        pause=pauses.append,
        clock=lambda: float(next(ticks)),
    )
    assert results["q1"] == {
        "id": "q1",
        "limit": 3,
        "status": "ok",
        "documents": ["hit for good"],
        "latency_ms": 1000.0,
    }
    assert results["q2"]["status"] == "error" and results["q2"]["documents"] == []
    assert "down" in results["q2"]["error"]
    assert pauses == [0.5, 0.5]

    healthy = True
    results = engines.run(Flaky(name="flaky"), records, journal, pause=pauses.append)
    assert results["q2"]["status"] == "ok"
    assert len(pauses) == 3
    assert len(journal.read_text().splitlines()) == 3
    assert engines.read_results(journal) == results
