"""Unit tests for one_agent.config."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.config import (
    Config,
    ConfigError,
    load_config,
)

_ALL_VARS = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")
_REQUIRED_VARS = ("OPENAI_BASE_URL", "OPENAI_MODEL")


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("one_agent.config.load_dotenv", lambda: None)
    for var in _ALL_VARS:
        monkeypatch.delenv(var, raising=False)


def _set_all(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")


class TestLoadConfig:
    def test_loads_all_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all(monkeypatch)

        config = load_config()

        assert config.openai_api_key == "sk-test-key"  # pragma: allowlist secret
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o"

    def test_strips_whitespace_from_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "  sk-test-key  ")
        monkeypatch.setenv("OPENAI_BASE_URL", "  https://api.openai.com/v1  ")
        monkeypatch.setenv("OPENAI_MODEL", "  gpt-4o  ")

        config = load_config()

        assert config.openai_api_key == "sk-test-key"  # pragma: allowlist secret
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o"

    @pytest.mark.parametrize("missing_var", _REQUIRED_VARS)
    def test_fails_on_missing_required_var(
        self, monkeypatch: pytest.MonkeyPatch, missing_var: str
    ) -> None:
        _set_all(monkeypatch)
        monkeypatch.delenv(missing_var)

        with pytest.raises(ConfigError, match=missing_var):
            load_config()

    def test_succeeds_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all(monkeypatch)
        monkeypatch.delenv("OPENAI_API_KEY")

        config = load_config()

        assert config.openai_api_key is None
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o"

    def test_blank_api_key_treated_as_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _set_all(monkeypatch)
        monkeypatch.setenv("OPENAI_API_KEY", "   ")

        config = load_config()

        assert config.openai_api_key is None

    def test_fails_on_all_required_missing(self) -> None:
        with pytest.raises(ConfigError, match="OPENAI_BASE_URL") as exc_info:
            load_config()

        assert "OPENAI_MODEL" in str(exc_info.value)

    def test_fails_on_blank_required_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_all(monkeypatch)
        monkeypatch.setenv("OPENAI_BASE_URL", "   ")

        with pytest.raises(ConfigError, match="OPENAI_BASE_URL"):
            load_config()


class TestConfig:
    def test_dataclass_fields(self) -> None:
        config = Config(
            openai_api_key="key",  # pragma: allowlist secret
            openai_base_url="https://api.openai.com/v1",
            openai_model="gpt-4o",
        )

        assert config.openai_api_key == "key"  # pragma: allowlist secret
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o"

    def test_frozen(self) -> None:
        config = Config(
            openai_api_key="key",  # pragma: allowlist secret
            openai_base_url="https://url",
            openai_model="model",
        )

        with pytest.raises(AttributeError):
            config.openai_api_key = "other"  # type: ignore[misc]
