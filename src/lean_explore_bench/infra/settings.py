"""Configuration read from the environment.

Secrets come only from environment variables (or a dotenv file the caller
points to), never from the repository.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def read_env_file(path: Path) -> dict[str, str]:
    """Parse a dotenv-style file of ``NAME=value`` lines.

    Args:
        path: The file to read.

    Returns:
        Variables defined in the file, with surrounding quotes removed.
        Comments, blank lines and ``export`` prefixes are handled.
    """
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().removeprefix("export ").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip("'\"")
    return values


@dataclass(frozen=True)
class OpenRouterSettings:
    """Settings for :class:`lean_explore_bench.infra.openrouter.OpenRouterClient`.

    Attributes:
        api_key: OpenRouter API key.
        base_url: API base URL.
        default_model: Model used when a request does not name one. There is
            no built-in default: set ``OPENROUTER_MODEL`` or pass a model.
        timeout_seconds: Per-request timeout.
        max_attempts: Attempts per request, including the first.
        max_concurrency: Requests allowed in flight at once.
        data_collection: OpenRouter provider routing. ``"deny"`` restricts
            requests to providers that do not store or train on prompts.
        app_title: Sent as ``X-Title`` so usage is attributed on OpenRouter.
        extra_provider: Further provider routing preferences, passed through.
    """

    api_key: str = field(repr=False)
    base_url: str = DEFAULT_BASE_URL
    default_model: str | None = None
    timeout_seconds: float = 120.0
    max_attempts: int = 5
    max_concurrency: int = 8
    data_collection: Literal["allow", "deny"] = "deny"
    app_title: str = "lean-explore-bench"
    extra_provider: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "OpenRouterSettings":
        """Build settings from environment variables.

        Reads ``OPENROUTER_API_KEY`` (required), and optionally
        ``OPENROUTER_BASE_URL``, ``OPENROUTER_MODEL`` and
        ``OPENROUTER_MAX_CONCURRENCY``. Process environment variables take
        precedence over ``env_file``.

        Args:
            env_file: Optional dotenv file to read as a fallback.

        Returns:
            The settings.

        Raises:
            KeyError: If no API key is configured.
            ValueError: If a numeric setting is out of range.
        """
        values = read_env_file(env_file) if env_file else {}
        values.update(
            {k: v for k, v in os.environ.items() if k.startswith("OPENROUTER_")}
        )
        if not values.get("OPENROUTER_API_KEY"):
            raise KeyError("OPENROUTER_API_KEY is not set")
        return cls(
            api_key=values["OPENROUTER_API_KEY"],
            base_url=values.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
            default_model=values.get("OPENROUTER_MODEL"),
            max_concurrency=int(values.get("OPENROUTER_MAX_CONCURRENCY", "8")),
        )

    def __post_init__(self) -> None:
        """Reject values that would hang or disable the client."""
        if self.max_concurrency < 1:
            raise ValueError(
                f"max_concurrency must be at least 1, not {self.max_concurrency}"
            )
        if self.max_attempts < 1:
            raise ValueError(
                f"max_attempts must be at least 1, not {self.max_attempts}"
            )
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"timeout_seconds must be positive, not {self.timeout_seconds}"
            )

    def provider_preferences(self) -> dict[str, object]:
        """Return the ``provider`` object sent with every request."""
        return {"data_collection": self.data_collection, **self.extra_provider}
