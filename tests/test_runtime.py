"""Unit tests for one_agent.runtime."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.config import Config
from one_agent.runtime import invoke


def _make_config(
    *,
    api_key: str | None = "sk-test",  # pragma: allowlist secret
    base_url: str = "https://api.example.com/v1",
    model: str = "gpt-4o",
) -> Config:
    return Config(openai_api_key=api_key, openai_base_url=base_url, openai_model=model)


class TestInvoke:
    @patch("one_agent.runtime.ChatOpenAI")
    def test_returns_model_response(self, mock_cls: MagicMock) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="The answer is 42.")
        mock_cls.return_value = mock_llm

        result = invoke(config=_make_config(), prompt="What is the answer?")

        assert result == "The answer is 42."
        mock_llm.invoke.assert_called_once_with("What is the answer?")

    @patch("one_agent.runtime.ChatOpenAI")
    def test_passes_api_key_when_present(self, mock_cls: MagicMock) -> None:
        mock_cls.return_value = MagicMock(
            invoke=MagicMock(return_value=MagicMock(content="ok"))
        )

        invoke(
            config=_make_config(api_key="sk-key"), prompt="hi"
        )  # pragma: allowlist secret

        _, kwargs = mock_cls.call_args
        assert kwargs["api_key"] == "sk-key"  # pragma: allowlist secret

    @patch("one_agent.runtime.ChatOpenAI")
    def test_omits_api_key_when_none(self, mock_cls: MagicMock) -> None:
        mock_cls.return_value = MagicMock(
            invoke=MagicMock(return_value=MagicMock(content="ok"))
        )

        invoke(config=_make_config(api_key=None), prompt="hi")

        _, kwargs = mock_cls.call_args
        assert "api_key" not in kwargs

    @patch("one_agent.runtime.ChatOpenAI")
    def test_passes_model_and_base_url(self, mock_cls: MagicMock) -> None:
        mock_cls.return_value = MagicMock(
            invoke=MagicMock(return_value=MagicMock(content="ok"))
        )

        invoke(
            config=_make_config(model="gpt-4o-mini", base_url="https://custom.api/v1"),
            prompt="hi",
        )

        _, kwargs = mock_cls.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["base_url"] == "https://custom.api/v1"
