import asyncio
import json

import httpx2 as httpx
import jsonschema
import openai
import pytest

from lean_explore_bench.infra import OpenRouterClient, OpenRouterSettings
from lean_explore_bench.infra.openrouter import EmptyCompletionError
from lean_explore_bench.infra.settings import read_env_file


def _reply(content: str | None, cost: float | None = 0.002) -> dict[str, object]:
    usage: dict[str, object] = {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "total_tokens": 18,
    }
    if cost is not None:
        usage["cost"] = cost
    return {
        "id": "gen-1",
        "object": "chat.completion",
        "created": 0,
        "model": "test/model",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": usage,
    }


class Server:
    """Scripted responses; records every request body."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.bodies: list[dict[str, object]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.bodies.append(json.loads(request.content))
        return self.responses.pop(0)


def _client(server: Server, **overrides: object) -> OpenRouterClient:
    settings = OpenRouterSettings(
        api_key="test-key", default_model="test/model", max_attempts=3, **overrides
    )
    http = httpx.AsyncClient(transport=httpx.MockTransport(server))
    return OpenRouterClient(settings, http_client=http)


def _run(coroutine):
    return asyncio.run(coroutine)


MESSAGES = [{"role": "user", "content": "hi"}]


def test_complete_returns_text_usage_and_routing():
    server = Server([httpx.Response(200, json=_reply("hello"))])

    async def go():
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


def test_retries_rate_limits_then_succeeds(monkeypatch):
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)
    server = Server(
        [
            httpx.Response(429, json={"error": {"message": "slow down"}}),
            httpx.Response(503, json={"error": {"message": "busy"}}),
            httpx.Response(200, json=_reply("ok")),
        ]
    )

    async def go():
        async with _client(server) as client:
            return await client.complete(MESSAGES)

    assert _run(go()).text == "ok"
    assert len(server.bodies) == 3


def test_does_not_retry_client_errors():
    server = Server([httpx.Response(400, json={"error": {"message": "bad"}})])

    async def go():
        async with _client(server) as client:
            await client.complete(MESSAGES)

    with pytest.raises(openai.BadRequestError):
        _run(go())
    assert len(server.bodies) == 1


SCHEMA = {
    "type": "object",
    "properties": {"queries": {"type": "array", "items": {"type": "string"}}},
    "required": ["queries"],
    "additionalProperties": False,
}


def test_complete_json_sends_schema_and_parses():
    server = Server([httpx.Response(200, json=_reply('{"queries": ["a", "b"]}'))])
    schema = SCHEMA

    async def go():
        async with _client(server) as client:
            return await client.complete_json(MESSAGES, schema, name="queries")

    assert _run(go()) == {"queries": ["a", "b"]}
    sent = server.bodies[0]["response_format"]
    assert sent["type"] == "json_schema"
    assert sent["json_schema"]["schema"] == schema


def test_complete_json_rejects_output_that_breaks_the_schema():
    server = Server([httpx.Response(200, json=_reply('{"queries": "not a list"}'))])

    async def go():
        async with _client(server) as client:
            return await client.complete_json(MESSAGES, SCHEMA)

    with pytest.raises(jsonschema.ValidationError):
        _run(go())


def test_backoff_does_not_hold_a_concurrency_slot(monkeypatch):
    server = Server(
        [
            httpx.Response(429, json={"error": {"message": "slow down"}}),
            httpx.Response(200, json=_reply("ok")),
        ]
    )
    client = _client(server, max_concurrency=1)
    held_while_sleeping = []

    async def sleep(_seconds: float) -> None:
        held_while_sleeping.append(client._semaphore.locked())

    monkeypatch.setattr(asyncio, "sleep", sleep)
    assert _run(client.complete(MESSAGES)).text == "ok"
    assert held_while_sleeping == [False]


@pytest.mark.parametrize(
    "overrides",
    [{"max_concurrency": 0}, {"max_attempts": 0}, {"timeout_seconds": 0}],
)
def test_settings_reject_values_that_would_hang(overrides):
    with pytest.raises(ValueError):
        OpenRouterSettings(api_key="k", **overrides)


def test_settings_reject_zero_concurrency_from_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("OPENROUTER_MAX_CONCURRENCY", "0")
    with pytest.raises(ValueError):
        OpenRouterSettings.from_env()


def test_complete_many_keeps_order_and_failures():
    server = Server(
        [
            httpx.Response(200, json=_reply("one")),
            httpx.Response(400, json={"error": {"message": "bad"}}),
            httpx.Response(200, json=_reply("three", cost=None)),
        ]
    )

    async def go():
        async with _client(server, max_concurrency=1) as client:
            return await client.complete_many([MESSAGES] * 3), client.usage

    results, usage = _run(go())
    assert results[0].text == "one"
    assert isinstance(results[1], openai.BadRequestError)
    assert results[2].text == "three" and results[2].cost is None
    assert usage.requests == 2


def test_empty_content_is_an_error():
    server = Server([httpx.Response(200, json=_reply(None))])

    async def go():
        async with _client(server) as client:
            await client.complete(MESSAGES)

    with pytest.raises(EmptyCompletionError):
        _run(go())


def test_model_is_required():
    server = Server([])
    settings = OpenRouterSettings(api_key="k")
    client = OpenRouterClient(
        settings, http_client=httpx.AsyncClient(transport=httpx.MockTransport(server))
    )
    with pytest.raises(ValueError):
        _run(client.complete(MESSAGES))


def test_settings_from_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# keys\nexport OPENROUTER_API_KEY='from-file'\n", encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model")
    settings = OpenRouterSettings.from_env(env)
    assert settings.api_key == "from-file"
    assert settings.default_model == "test/model"
    assert "from-file" not in repr(settings)
    assert read_env_file(env) == {"OPENROUTER_API_KEY": "from-file"}

    monkeypatch.setenv("OPENROUTER_API_KEY", "from-env")
    assert OpenRouterSettings.from_env(env).api_key == "from-env"


def test_settings_require_a_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(KeyError):
        OpenRouterSettings.from_env()


async def _no_sleep(_seconds: float) -> None:
    return None
