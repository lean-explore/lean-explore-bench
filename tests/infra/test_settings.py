from pathlib import Path
from typing import Any

import pytest

from lean_explore_bench.infra.settings import OpenRouterSettings, read_env_file


@pytest.mark.parametrize(
    "overrides",
    [{"max_concurrency": 0}, {"max_attempts": 0}, {"timeout_seconds": 0}],
)
def test_reject_values_that_would_hang(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        OpenRouterSettings(api_key="k", **overrides)


def test_reject_zero_concurrency_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("OPENROUTER_MAX_CONCURRENCY", "0")
    with pytest.raises(ValueError):
        OpenRouterSettings.from_env()


def test_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / ".env"
    env.write_text("# keys\nexport OPENROUTER_API_KEY='from-file'\n", encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model")
    settings = OpenRouterSettings.from_env(env)
    assert settings.api_key == "from-file"
    assert settings.default_model == "test/model"
    assert "from-file" not in repr(settings)
    monkeypatch.setenv("OPENROUTER_API_KEY", "from-env")
    assert OpenRouterSettings.from_env(env).api_key == "from-env"


def test_require_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(KeyError):
        OpenRouterSettings.from_env()


def test_provider_preferences_merge_extras() -> None:
    settings = OpenRouterSettings(api_key="k", extra_provider={"sort": "price"})
    assert settings.provider_preferences() == {
        "data_collection": "deny",
        "sort": "price",
    }


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("A=4 # workers", "4"),
        ('A="key" # account', "key"),
        ("A='key' # account", "key"),
        ('A="has # inside"', "has # inside"),
        ("A=no#space", "no#space"),
        ("A=  spaced  ", "spaced"),
        ('A="unterminated', "unterminated"),
        ("export A=1", "1"),
        ("A=", ""),
    ],
)
def test_env_file_values(tmp_path: Path, line: str, expected: str) -> None:
    env = tmp_path / ".env"
    env.write_text(f"# header\n\nnot a variable\n{line}\n", encoding="utf-8")
    assert read_env_file(env) == {"A": expected}


def test_from_env_file_with_inline_comments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = tmp_path / ".env"
    env.write_text(
        'OPENROUTER_API_KEY="secret" # account\nOPENROUTER_MAX_CONCURRENCY=4 # n\n',
        encoding="utf-8",
    )
    for name in ("OPENROUTER_API_KEY", "OPENROUTER_MAX_CONCURRENCY"):
        monkeypatch.delenv(name, raising=False)
    settings = OpenRouterSettings.from_env(env)
    assert settings.api_key == "secret"
    assert settings.max_concurrency == 4
