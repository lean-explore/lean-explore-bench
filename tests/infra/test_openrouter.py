import asyncio
import json
from collections.abc import Coroutine
from typing import Any, TypeVar

import httpx2 as httpx
import jsonschema
import openai
import pytest
from openai.types.chat import ChatCompletionMessageParam

from lean_explore_bench.infra import (
    Completion,
    OpenRouterClient,
    OpenRouterSettings,
    UsageTotals,
)
from lean_explore_bench.infra.openrouter import EmptyCompletionError

T = TypeVar("T")

MESSAGES: list[ChatCompletionMessageParam] = [{"role": "user", "content": "hi"}]

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"queries": {"type": "array", "items": {"type": "string"}}},
    "required": ["queries"],
    "additionalProperties": False,
}


def _reply(content: str | None, cost: float | None = 0.002) -> dict[str, Any]:
    usage: dict[str, Any] = {"prompt_tokens": 11, "completion_tokens": 7}
    usage["total_tokens"] = 18
    if cost is not None:
        usage["cost"] = cost
    message = {"role": "assistant", "content": content}
    return {
        "id": "gen-1",
        "object": "chat.completion",
        "created": 0,
        "model": "test/model",
        "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
        "usage": usage,
    }


def _error(status: int) -> httpx.Response:
    return httpx.Response(status, json={"error": {"message": "failed"}})


class Server:
    """Scripted responses; records every request body."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.bodies: list[dict[str, Any]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.bodies.append(json.loads(request.content))
        return self.responses.pop(0)


def _client(server: Server, **overrides: Any) -> OpenRouterClient:
    settings = OpenRouterSettings(
        api_key="test-key", default_model="test/model", max_attempts=3, **overrides
    )
    http = httpx.AsyncClient(transport=httpx.MockTransport(server))
    return OpenRouterClient(settings, http_client=http)


def _run(coroutine: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coroutine)


async def _no_sleep(_seconds: float) -> None:
    return None


def test_complete_returns_text_usage_and_routing() -> None:
    server = Server([httpx.Response(200, json=_reply("hello"))])

    async def go() -> tuple[Completion, UsageTotals]:
        async with _client(server) as client:
            return await client.complete(MESSAGES), client.usage

    completion, usage = _run(go())
    assert completion.text == "hello"
    assert (completion.prompt_tokens, completion.completion_tokens) == (11, 7)
    assert completion.cost == pytest.approx(0.002)
    assert usage.requests == 1 and usage.cost == pytest.approx(0.002)
    body = server.bodies[0]
    assert body["model"] == "test/model"
    assert body["provider"] == {"data_collection": "deny"}
    assert body["usage"] == {"include": True}


def test_retries_rate_limits_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)
    server = Server([_error(429), _error(503), httpx.Response(200, json=_reply("ok"))])
    assert _run(_client(server).complete(MESSAGES)).text == "ok"
    assert len(server.bodies) == 3


def test_does_not_retry_client_errors() -> None:
    server = Server([_error(400)])
    with pytest.raises(openai.BadRequestError):
        _run(_client(server).complete(MESSAGES))
    assert len(server.bodies) == 1


def test_backoff_does_not_hold_a_concurrency_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = Server([_error(429), httpx.Response(200, json=_reply("ok"))])
    client = _client(server, max_concurrency=1)
    held_while_sleeping: list[bool] = []

    async def sleep(_seconds: float) -> None:
        held_while_sleeping.append(client._semaphore.locked())

    monkeypatch.setattr(asyncio, "sleep", sleep)
    assert _run(client.complete(MESSAGES)).text == "ok"
    assert held_while_sleeping == [False]


def test_complete_json_sends_schema_and_parses() -> None:
    server = Server([httpx.Response(200, json=_reply('{"queries": ["a", "b"]}'))])
    result = _run(_client(server).complete_json(MESSAGES, SCHEMA, name="queries"))
    assert result == {"queries": ["a", "b"]}
    sent = server.bodies[0]["response_format"]
    assert sent["type"] == "json_schema"
    assert sent["json_schema"]["schema"] == SCHEMA


def test_complete_json_rejects_output_that_breaks_the_schema() -> None:
    server = Server([httpx.Response(200, json=_reply('{"queries": "not a list"}'))])
    with pytest.raises(jsonschema.ValidationError):
        _run(_client(server).complete_json(MESSAGES, SCHEMA))


def test_complete_many_keeps_order_and_failures() -> None:
    server = Server(
        [
            httpx.Response(200, json=_reply("one")),
            _error(400),
            httpx.Response(200, json=_reply("three", cost=None)),
        ]
    )
    client = _client(server, max_concurrency=1)
    first, second, third = _run(client.complete_many([MESSAGES] * 3))
    assert isinstance(first, Completion) and first.text == "one"
    assert isinstance(second, openai.BadRequestError)
    assert isinstance(third, Completion) and third.cost is None
    assert client.usage.requests == 2


def test_empty_content_is_an_error_but_still_billed() -> None:
    server = Server([httpx.Response(200, json=_reply(None))])
    client = _client(server)
    with pytest.raises(EmptyCompletionError):
        _run(client.complete(MESSAGES))
    usage = client.usage
    assert (usage.requests, usage.prompt_tokens, usage.completion_tokens) == (1, 11, 7)
    assert usage.cost == pytest.approx(0.002)


def test_missing_usage_block_counts_as_zero() -> None:
    reply = _reply("hi")
    del reply["usage"]
    client = _client(Server([httpx.Response(200, json=reply)]))
    completion = _run(client.complete(MESSAGES))
    assert (completion.prompt_tokens, completion.completion_tokens) == (0, 0)
    assert completion.cost is None


def test_model_is_required() -> None:
    http = httpx.AsyncClient(transport=httpx.MockTransport(Server([])))
    client = OpenRouterClient(OpenRouterSettings(api_key="k"), http_client=http)
    with pytest.raises(ValueError):
        _run(client.complete(MESSAGES))
