"""Unit tests for one_agent.runtime."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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

    @patch("one_agent.runtime.ChatOpenAI")
    def test_system_instructions_sent_as_system_message(
        self, mock_cls: MagicMock
    ) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="ok")
        mock_cls.return_value = mock_llm

        invoke(
            config=_make_config(),
            prompt="hi",
            system_instructions="Follow the writer skill.",
        )

        mock_llm.invoke.assert_called_once_with(
            [("system", "Follow the writer skill."), ("human", "hi")]
        )

    @patch("one_agent.runtime.ChatOpenAI")
    def test_empty_system_instructions_falls_back_to_plain_prompt(
        self, mock_cls: MagicMock
    ) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="ok")
        mock_cls.return_value = mock_llm

        invoke(config=_make_config(), prompt="hi", system_instructions="")

        mock_llm.invoke.assert_called_once_with("hi")

    @patch("one_agent.runtime.create_react_agent")
    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_mcp_servers_trigger_react_agent_and_return_final_message(
        self,
        mock_cls: MagicMock,
        mock_client_cls: MagicMock,
        mock_create_agent: MagicMock,
    ) -> None:
        from one_agent.mcp_config import McpServer

        mock_cls.return_value = MagicMock()
        tool = MagicMock(name="tool")
        client = MagicMock()

        async def _get_tools() -> list[object]:
            return [tool]

        client.get_tools = _get_tools
        mock_client_cls.return_value = client

        agent = MagicMock()

        async def _ainvoke(state: dict) -> dict:
            return {"messages": [MagicMock(content="agent answer")]}

        agent.ainvoke = _ainvoke
        mock_create_agent.return_value = agent

        result = invoke(
            config=_make_config(),
            prompt="search the web",
            system_instructions="use tools wisely",
            mcp_servers=[McpServer(name="tavily", command="npx")],
        )

        assert result == "agent answer"
        connections = mock_client_cls.call_args.args[0]
        assert list(connections.keys()) == ["tavily"]
        args, kwargs = mock_create_agent.call_args
        assert args[1] == [tool]
        assert kwargs["prompt"] == "use tools wisely"

    @patch("one_agent.runtime.create_react_agent")
    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_no_mcp_servers_does_not_invoke_agent(
        self,
        mock_cls: MagicMock,
        mock_client_cls: MagicMock,
        mock_create_agent: MagicMock,
    ) -> None:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="plain")
        mock_cls.return_value = mock_llm

        result = invoke(config=_make_config(), prompt="hi", mcp_servers=[])

        assert result == "plain"
        mock_create_agent.assert_not_called()
        mock_client_cls.assert_not_called()

    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_mcp_startup_failure_raises_mcp_server_error(
        self, mock_cls: MagicMock, mock_client_cls: MagicMock
    ) -> None:
        from one_agent.mcp_config import McpServer
        from one_agent.mcp_servers import McpServerError

        mock_cls.return_value = MagicMock()
        client = MagicMock()

        async def _boom() -> list[object]:
            raise RuntimeError("npx not found")

        client.get_tools = _boom
        mock_client_cls.return_value = client

        with pytest.raises(
            McpServerError, match=r"/tavily.*RuntimeError.*npx not found"
        ):
            invoke(
                config=_make_config(),
                prompt="hi",
                mcp_servers=[McpServer(name="tavily", command="npx")],
            )
