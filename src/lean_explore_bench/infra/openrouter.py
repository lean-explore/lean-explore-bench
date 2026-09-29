"""Async OpenRouter client with retries, concurrency limits and usage totals.

Wraps OpenRouter's OpenAI-compatible chat completions API, as lean-explore's
``util/openrouter_client.py`` does, and adds what batch generation needs:

- retries with exponential backoff on rate limits, timeouts, connection
  errors and server errors (other errors fail at once);
- a cap on requests in flight;
- JSON output checked against a schema via ``response_format``;
- running token and cost totals across all calls;
- provider routing that, by default, avoids providers that store or train
  on prompts (``data_collection: "deny"``).

Example::

    settings = OpenRouterSettings.from_env()
    async with OpenRouterClient(settings) as client:
        completion = await client.complete(
            [{"role": "user", "content": "Say hello."}], model="some/model"
        )
"""

import asyncio
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

import httpx2
import jsonschema
import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from lean_explore_bench.infra.settings import OpenRouterSettings

RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.InternalServerError,
)


class EmptyCompletionError(RuntimeError):
    """The API returned no message content."""


@dataclass(frozen=True)
class Completion:
    """One chat completion.

    Attributes:
        text: The assistant message content.
        model: The model that answered, as reported by OpenRouter.
        prompt_tokens: Input tokens.
        completion_tokens: Output tokens.
        cost: Cost in USD, when OpenRouter reports it.
    """

    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float | None


@dataclass(frozen=True)
class ResponseUsage:
    """Tokens and cost billed for one response, whatever its content.

    Attributes:
        prompt_tokens: Input tokens.
        completion_tokens: Output tokens.
        cost: Cost in USD, when OpenRouter reports it.
    """

    prompt_tokens: int
    completion_tokens: int
    cost: float | None

    @classmethod
    def of(cls, response: ChatCompletion) -> "ResponseUsage":
        """Read the usage block of a response (zeros when it is missing)."""
        usage = response.usage
        if usage is None:
            return cls(0, 0, None)
        cost = (usage.model_extra or {}).get("cost")
        return cls(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cost=float(cost) if isinstance(cost, int | float) else None,
        )


@dataclass
class UsageTotals:
    """Running totals over every response a client received.

    Responses rejected afterwards (for example with no content) still count,
    because they were billed.
    """

    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def add(self, usage: ResponseUsage) -> None:
        """Add one response's usage to the totals."""
        async with self._lock:
            self.requests += 1
            self.prompt_tokens += usage.prompt_tokens
            self.completion_tokens += usage.completion_tokens
            self.cost += usage.cost or 0.0


def _to_completion(response: ChatCompletion, usage: ResponseUsage) -> Completion:
    content = response.choices[0].message.content if response.choices else None
    if content is None:
        raise EmptyCompletionError(f"No content in response from {response.model}")
    return Completion(
        text=content,
        model=response.model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cost=usage.cost,
    )


class OpenRouterClient:
    """Chat completions through OpenRouter.

    Use as an async context manager so the HTTP connection pool is closed.
    """

    def __init__(
        self,
        settings: OpenRouterSettings,
        http_client: httpx2.AsyncClient | None = None,
    ) -> None:
        """Create a client.

        Args:
            settings: Connection, retry and routing settings.
            http_client: Optional HTTP client, e.g. with a mock transport in
                tests.
        """
        self.settings = settings
        self.usage = UsageTotals()
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)
        self._client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            max_retries=0,
            default_headers={"X-Title": settings.app_title},
            http_client=http_client,
        )

    async def __aenter__(self) -> "OpenRouterClient":
        """Enter the context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()

    def _body(self, response_format: dict[str, Any] | None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "provider": self.settings.provider_preferences(),
            "usage": {"include": True},
        }
        if response_format is not None:
            body["response_format"] = response_format
        return body

    async def _request(
        self,
        messages: Sequence[ChatCompletionMessageParam],
        model: str,
        temperature: float,
        max_tokens: int | None,
        response_format: dict[str, Any] | None,
    ) -> ChatCompletion:
        return await self._client.chat.completions.create(
            model=model,
            messages=list(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=self._body(response_format),
        )

    async def complete(
        self,
        messages: Sequence[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> Completion:
        """Request one chat completion, retrying transient failures.

        Args:
            messages: Chat messages.
            model: OpenRouter model id; defaults to the settings' model.
            temperature: Sampling temperature.
            max_tokens: Output token limit.
            response_format: Optional OpenAI-style ``response_format``.

        Returns:
            The :class:`Completion`.

        Raises:
            ValueError: If no model is given or configured.
        """
        model = model or self.settings.default_model
        if model is None:
            raise ValueError("No model given and OPENROUTER_MODEL is not set")
        retrying = AsyncRetrying(
            retry=retry_if_exception_type(RETRYABLE_ERRORS),
            stop=stop_after_attempt(self.settings.max_attempts),
            wait=wait_exponential_jitter(initial=1, max=30),
            reraise=True,
        )
        # Hold a concurrency slot only while a request is in flight, so a
        # request backing off after a rate limit does not block others.
        async for attempt in retrying:
            with attempt:
                async with self._semaphore:
                    response = await self._request(
                        messages, model, temperature, max_tokens, response_format
                    )
        usage = ResponseUsage.of(response)
        await self.usage.add(usage)
        return _to_completion(response, usage)

    async def complete_json(
        self,
        messages: Sequence[ChatCompletionMessageParam],
        schema: dict[str, Any],
        name: str = "response",
        **kwargs: Any,
    ) -> Any:
        """Request a completion constrained to a JSON schema, then check it.

        The schema is sent as ``response_format``, but providers do not all
        enforce it, so the parsed value is also validated locally.

        Args:
            messages: Chat messages.
            schema: JSON schema the output must follow.
            name: Schema name sent to the API.
            **kwargs: Passed to :meth:`complete`.

        Returns:
            The parsed JSON value, guaranteed to match ``schema``.

        Raises:
            json.JSONDecodeError: If the model returned invalid JSON.
            jsonschema.ValidationError: If the JSON does not match ``schema``.
        """
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": name, "strict": True, "schema": schema},
        }
        completion = await self.complete(
            messages, response_format=response_format, **kwargs
        )
        value = json.loads(completion.text)
        jsonschema.validate(value, schema)
        return value

    async def complete_many(
        self,
        requests: Sequence[Sequence[ChatCompletionMessageParam]],
        **kwargs: Any,
    ) -> list[Completion | BaseException]:
        """Run many completions concurrently, within the concurrency cap.

        Args:
            requests: One message list per request.
            **kwargs: Passed to :meth:`complete` for every request.

        Returns:
            One result per request, in order. Failed requests hold their
            exception instead of raising, so one failure does not lose the
            rest of a batch.
        """
        return await asyncio.gather(
            *(self.complete(messages, **kwargs) for messages in requests),
            return_exceptions=True,
        )
