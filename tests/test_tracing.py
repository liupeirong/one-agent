"""Tests for optional LangSmith tracing configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.tracing import TracingConfig, configure_tracing


class TestConfigureTracing:
    def test_no_api_key_keeps_tracing_disabled(self) -> None:
        env: dict[str, str] = {}

        result = configure_tracing(env)

        assert result == TracingConfig(enabled=False)
        assert "LANGSMITH_TRACING" not in env
        assert "LANGCHAIN_TRACING_V2" not in env

    def test_api_key_present_enables_tracing(self) -> None:
        env = {"LANGSMITH_API_KEY": "ls-test"}  # pragma: allowlist secret

        result = configure_tracing(env)

        assert result.enabled is True
        assert env["LANGSMITH_TRACING"] == "true"
        assert env["LANGCHAIN_TRACING_V2"] == "true"

    def test_legacy_langchain_api_key_enables_tracing(self) -> None:
        env = {"LANGCHAIN_API_KEY": "ls-test"}  # pragma: allowlist secret

        result = configure_tracing(env)

        assert result.enabled is True
        assert env["LANGSMITH_TRACING"] == "true"

    def test_blank_api_key_keeps_tracing_disabled(self) -> None:
        env = {"LANGSMITH_API_KEY": "   "}

        result = configure_tracing(env)

        assert result.enabled is False
        assert "LANGSMITH_TRACING" not in env

    def test_explicit_disable_overrides_api_key(self) -> None:
        env = {
            "LANGSMITH_API_KEY": "ls-test",  # pragma: allowlist secret
            "LANGSMITH_TRACING": "false",
        }

        result = configure_tracing(env)

        assert result.enabled is False
        assert env["LANGSMITH_TRACING"] == "false"
        assert "LANGCHAIN_TRACING_V2" not in env

    def test_explicit_disable_recognized_zero(self) -> None:
        env = {
            "LANGSMITH_API_KEY": "ls-test",  # pragma: allowlist secret
            "LANGSMITH_TRACING": "0",
        }

        assert configure_tracing(env).enabled is False

    def test_legacy_langchain_tracing_disable_is_honored(self) -> None:
        # Users migrating from legacy LangChain tracing may have
        # LANGCHAIN_TRACING_V2=false set in their shell to suppress
        # tracing. Honor it like the new-style flag.
        env = {
            "LANGSMITH_API_KEY": "ls-test",  # pragma: allowlist secret
            "LANGCHAIN_TRACING_V2": "false",
        }

        result = configure_tracing(env)

        assert result.enabled is False
        assert env["LANGCHAIN_TRACING_V2"] == "false"

    def test_explicit_enable_is_respected(self) -> None:
        env = {
            "LANGSMITH_API_KEY": "ls-test",  # pragma: allowlist secret
            "LANGSMITH_TRACING": "true",
        }

        result = configure_tracing(env)

        assert result.enabled is True
        assert env["LANGSMITH_TRACING"] == "true"
        assert env["LANGCHAIN_TRACING_V2"] == "true"

    def test_stale_tracing_true_without_key_is_normalized_to_false(self) -> None:
        # If a shell leaves LANGSMITH_TRACING=true exported but no key
        # is available, downstream LangChain code must not see a stale
        # "true" and attempt unauthenticated exports.
        env = {"LANGSMITH_TRACING": "true"}

        result = configure_tracing(env)

        assert result.enabled is False
        assert env["LANGSMITH_TRACING"] == "false"

    def test_defaults_to_os_environ_when_env_omitted(self, monkeypatch) -> None:
        monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
        monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
        monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
        monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)

        result = configure_tracing()

        assert result.enabled is False
