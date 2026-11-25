"""A scripted language model for the query mix tests."""

import json
from collections.abc import Callable
from typing import Any

import httpx2 as httpx

from lean_explore_bench.builder.llm import OpenRouterClient, OpenRouterSettings

Responder = Callable[[dict[str, Any]], str]


def scripted_client(respond: Responder) -> OpenRouterClient:
    """A client whose replies are computed from the request body."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        message = {"role": "assistant", "content": respond(body)}
        return httpx.Response(
            200,
            json={
                "id": "gen-1",
                "object": "chat.completion",
                "created": 0,
                "model": body["model"],
                "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                    "cost": 0.001,
                },
            },
        )

    settings = OpenRouterSettings(api_key="test-key", max_attempts=1)
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenRouterClient(settings, http_client=http)


def system_of(body: dict[str, Any]) -> str:
    return str(body["messages"][0]["content"])


def user_of(body: dict[str, Any]) -> str:
    return str(body["messages"][1]["content"])
