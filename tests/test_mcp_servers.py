"""Tests for MCP tool loading."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.mcp_config import McpServer
from one_agent.mcp_servers import (
    McpServerError,
    load_mcp_tools,
    to_stdio_connection,
)


class TestToStdioConnection:
    def test_builds_minimal_connection(self) -> None:
        server = McpServer(name="x", command="run")
        conn = to_stdio_connection(server)
        assert conn == {"transport": "stdio", "command": "run", "args": []}

    def test_includes_args_and_env(self) -> None:
        server = McpServer(name="x", command="run", args=("--flag",), env={"K": "V"})
        conn = to_stdio_connection(server)
        assert conn == {
            "transport": "stdio",
            "command": "run",
            "args": ["--flag"],
            "env": {"K": "V"},
        }


class TestLoadMcpTools:
    def test_empty_servers_returns_empty_list(self) -> None:
        assert load_mcp_tools(()) == []

    @patch("one_agent.mcp_servers.MultiServerMCPClient")
    def test_passes_stdio_connections_and_returns_tools(
        self, mock_client_cls: MagicMock
    ) -> None:
        tool_a = MagicMock(name="tool_a")
        tool_b = MagicMock(name="tool_b")
        instance = MagicMock()

        async def _get_tools() -> list[object]:
            return [tool_a, tool_b]

        instance.get_tools = _get_tools
        mock_client_cls.return_value = instance

        servers = (
            McpServer(name="tavily", command="npx", args=("-y", "tavily-mcp")),
            McpServer(name="local", command="node", env={"X": "1"}),
        )

        tools = load_mcp_tools(servers)

        assert tools == [tool_a, tool_b]
        connections = mock_client_cls.call_args.args[0]
        assert set(connections.keys()) == {"tavily", "local"}
        assert connections["tavily"]["command"] == "npx"
        assert connections["tavily"]["args"] == ["-y", "tavily-mcp"]
        assert connections["local"]["env"] == {"X": "1"}

    @patch("one_agent.mcp_servers.MultiServerMCPClient")
    def test_startup_failure_raises_mcp_server_error(
        self, mock_client_cls: MagicMock
    ) -> None:
        instance = MagicMock()

        async def _boom() -> list[object]:
            raise RuntimeError("npx not found")

        instance.get_tools = _boom
        mock_client_cls.return_value = instance

        with pytest.raises(
            McpServerError, match=r"/tavily.*RuntimeError.*npx not found"
        ):
            load_mcp_tools((McpServer(name="tavily", command="npx"),))
