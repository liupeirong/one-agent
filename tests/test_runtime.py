"""Unit tests for one_agent.runtime."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.config import Config
from one_agent.mcp_config import McpServer
from one_agent.runtime import invoke


def _make_config(
    *,
    api_key: str | None = "sk-test",  # pragma: allowlist secret
    base_url: str = "https://api.example.com/v1",
    model: str = "gpt-4o",
) -> Config:
    return Config(openai_api_key=api_key, openai_base_url=base_url, openai_model=model)


def _make_mcp_client(*, tools: list[object]) -> MagicMock:
    """Build a MultiServerMCPClient mock whose get_tools() is awaitable.

    NOTE: Mirrors the real langchain-mcp-adapters 0.1.0+ API where the client
    is used directly (not as an async context manager). Do not wrap this mock
    in __aenter__/__aexit__.
    """
    client = MagicMock()

    async def _get_tools() -> list[object]:
        return tools

    client.get_tools = _get_tools
    return client


def _make_agent(*, messages: list[object]) -> MagicMock:
    agent = MagicMock()

    async def _ainvoke(_state: dict) -> dict:
        return {"messages": messages}

    agent.ainvoke = _ainvoke
    return agent


class TestInvoke:
    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_returns_final_agent_message(
        self, mock_cls: MagicMock, mock_create_agent: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_create_agent.return_value = _make_agent(
            messages=[MagicMock(content="The answer is 42.")]
        )

        result = invoke(config=_make_config(), prompt="What is the answer?")

        assert result == "The answer is 42."
        args, kwargs = mock_create_agent.call_args
        assert args[1] == []
        assert kwargs["system_prompt"] is None

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_no_mcp_servers_still_uses_agent_path(
        self, mock_cls: MagicMock, mock_create_agent: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_create_agent.return_value = _make_agent(
            messages=[MagicMock(content="plain")]
        )

        result = invoke(config=_make_config(), prompt="hi", mcp_servers=[])

        assert result == "plain"
        mock_create_agent.assert_called_once()

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_no_mcp_servers_does_not_touch_mcp_client(
        self, mock_cls: MagicMock, mock_create_agent: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_create_agent.return_value = _make_agent(messages=[MagicMock(content="ok")])

        with patch("one_agent.runtime.MultiServerMCPClient") as mock_client_cls:
            invoke(config=_make_config(), prompt="hi")

        mock_client_cls.assert_not_called()

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_passes_api_key_when_present(
        self, mock_cls: MagicMock, mock_create_agent: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_create_agent.return_value = _make_agent(messages=[MagicMock(content="ok")])

        invoke(
            config=_make_config(api_key="sk-key"), prompt="hi"
        )  # pragma: allowlist secret

        _, kwargs = mock_cls.call_args
        assert kwargs["api_key"] == "sk-key"  # pragma: allowlist secret

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_passes_model_and_base_url(
        self, mock_cls: MagicMock, mock_create_agent: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_create_agent.return_value = _make_agent(messages=[MagicMock(content="ok")])

        invoke(
            config=_make_config(model="gpt-4o-mini", base_url="https://custom.api/v1"),
            prompt="hi",
        )

        _, kwargs = mock_cls.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["base_url"] == "https://custom.api/v1"

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_system_instructions_are_passed_as_system_prompt(
        self, mock_cls: MagicMock, mock_create_agent: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_create_agent.return_value = _make_agent(messages=[MagicMock(content="ok")])

        invoke(
            config=_make_config(),
            prompt="hi",
            system_instructions="Follow the writer skill.",
        )

        _, kwargs = mock_create_agent.call_args
        assert kwargs["system_prompt"] == "Follow the writer skill."

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_empty_system_instructions_pass_none_system_prompt(
        self, mock_cls: MagicMock, mock_create_agent: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_create_agent.return_value = _make_agent(messages=[MagicMock(content="ok")])

        invoke(config=_make_config(), prompt="hi", system_instructions="")

        _, kwargs = mock_create_agent.call_args
        assert kwargs["system_prompt"] is None

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_mcp_servers_trigger_agent_and_return_final_message(
        self,
        mock_cls: MagicMock,
        mock_client_cls: MagicMock,
        mock_create_agent: MagicMock,
    ) -> None:
        mock_cls.return_value = MagicMock()
        tool = MagicMock(name="tool")
        mock_client_cls.return_value = _make_mcp_client(tools=[tool])
        mock_create_agent.return_value = _make_agent(
            messages=[MagicMock(content="agent answer")]
        )

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
        assert kwargs["system_prompt"] == "use tools wisely"

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_mcp_servers_pass_none_system_prompt_when_instructions_empty(
        self,
        mock_cls: MagicMock,
        mock_client_cls: MagicMock,
        mock_create_agent: MagicMock,
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_client_cls.return_value = _make_mcp_client(tools=[])
        mock_create_agent.return_value = _make_agent(
            messages=[MagicMock(content="done")]
        )

        invoke(
            config=_make_config(),
            prompt="hi",
            system_instructions="",
            mcp_servers=[McpServer(name="tavily", command="npx")],
        )

        _, kwargs = mock_create_agent.call_args
        assert kwargs["system_prompt"] is None

    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_mcp_startup_failure_propagates_raw_error(
        self, mock_cls: MagicMock, mock_client_cls: MagicMock
    ) -> None:
        mock_cls.return_value = MagicMock()
        client = MagicMock()

        async def _boom() -> list[object]:
            raise RuntimeError("npx not found")

        client.get_tools = _boom
        mock_client_cls.return_value = client

        with pytest.raises(RuntimeError, match="npx not found"):
            invoke(
                config=_make_config(),
                prompt="hi",
                mcp_servers=[McpServer(name="tavily", command="npx")],
            )

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_returns_empty_when_agent_yields_no_messages(
        self,
        mock_cls: MagicMock,
        mock_client_cls: MagicMock,
        mock_create_agent: MagicMock,
    ) -> None:
        mock_cls.return_value = MagicMock()
        mock_client_cls.return_value = _make_mcp_client(tools=[])
        mock_create_agent.return_value = _make_agent(messages=[])

        result = invoke(
            config=_make_config(),
            prompt="hi",
            mcp_servers=[McpServer(name="tavily", command="npx")],
        )

        assert result == ""

    @patch("one_agent.runtime.create_agent")
    @patch("one_agent.runtime.MultiServerMCPClient")
    @patch("one_agent.runtime.ChatOpenAI")
    def test_returns_last_message_after_multiple_internal_tool_calls(
        self,
        mock_cls: MagicMock,
        mock_client_cls: MagicMock,
        mock_create_agent: MagicMock,
    ) -> None:
        mock_cls.return_value = MagicMock()
        tool_a = MagicMock(name="tool_a")
        tool_b = MagicMock(name="tool_b")
        mock_client_cls.return_value = _make_mcp_client(tools=[tool_a, tool_b])
        mock_create_agent.return_value = _make_agent(
            messages=[
                MagicMock(content="tool_call_1"),
                MagicMock(content="tool_call_2"),
                MagicMock(content="final answer"),
            ]
        )

        result = invoke(
            config=_make_config(),
            prompt="research and summarize",
            mcp_servers=[McpServer(name="tavily", command="npx")],
        )

        assert result == "final answer"
        args, _kwargs = mock_create_agent.call_args
        assert args[1] == [tool_a, tool_b]
