"""Load LangChain tools from explicitly mentioned MCP servers.

This module wraps :class:`langchain_mcp_adapters.client.MultiServerMCPClient`
to translate validated :class:`McpServer` records into ready-to-use
LangChain :class:`BaseTool` instances. The synchronous
:func:`load_mcp_tools` helper is convenient for callers that only need
the tools (for example tests); the runtime instead lists tools and runs
the agent within a single event loop so adapter sessions stay alive
across the whole run.
"""

import asyncio
from typing import Iterable

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

from one_agent.mcp_config import McpServer


class McpServerError(Exception):
    """Raised when an MCP server cannot be started or its tools cannot be listed."""


def to_stdio_connection(server: McpServer) -> StdioConnection:
    """Translate a validated :class:`McpServer` into an adapter connection dict."""
    connection: StdioConnection = {
        "transport": "stdio",
        "command": server.command,
        "args": list(server.args),
    }
    if server.env:
        connection["env"] = dict(server.env)
    return connection


def load_mcp_tools(servers: Iterable[McpServer]) -> list[BaseTool]:
    """Return all tools exposed by *servers*.

    The MCP adapter is invoked once per call. Expected lifecycle errors
    (process spawn failures, transport errors) raise
    :class:`McpServerError`; programmer errors are not re-wrapped.
    """
    server_list = tuple(servers)
    if not server_list:
        return []

    connections: dict[str, StdioConnection] = {
        server.name: to_stdio_connection(server) for server in server_list
    }
    client = MultiServerMCPClient(connections)
    server_label = ", ".join(f"/{server.name}" for server in server_list)

    try:
        return asyncio.run(client.get_tools())
    except (OSError, RuntimeError, ConnectionError) as exc:
        raise McpServerError(
            f"Failed to load tools from MCP server(s) {server_label} "
            f"({type(exc).__name__}): {exc}."
        ) from exc
