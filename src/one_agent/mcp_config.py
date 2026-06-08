"""Parse Claude-style MCP server configuration from ``~/.claude.json``.

This module handles only configuration loading and validation. Starting
the MCP server processes and exposing their tools to the agent is the
responsibility of :mod:`one_agent.mcp_servers`.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TOP_LEVEL_KEY = "mcpServers"
_ALLOWED_TRANSPORTS = ("stdio",)


class McpConfigError(Exception):
    """Raised when ``~/.claude.json`` cannot be parsed or contains invalid entries."""


@dataclass(frozen=True)
class McpServer:
    """A validated stdio MCP server configuration entry.

    Only command-based stdio servers are supported in v1. The ``env``
    mapping is forwarded verbatim to the child process; secrets that
    live in it must be managed by the user.
    """

    name: str
    command: str
    args: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)


def default_mcp_config_path() -> Path:
    """Return the conventional Claude-style MCP configuration file path."""
    return Path.home() / ".claude.json"


def load_mcp_config(path: Path | None = None) -> dict[str, McpServer]:
    """Load and validate MCP server entries from a Claude-style config file.

    Returns an empty mapping when the configuration file does not exist or
    when it has no ``mcpServers`` object. Each remaining entry must be a
    command-based stdio server; non-stdio transports and malformed
    entries raise :class:`McpConfigError` so the run fails fast.
    """
    config_path = path if path is not None else default_mcp_config_path()
    if not config_path.is_file():
        return {}

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise McpConfigError(
            f"Failed to read MCP config at {config_path}: {exc}."
        ) from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise McpConfigError(
            f"Invalid JSON in MCP config at {config_path}: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})."
        ) from exc

    if not isinstance(data, dict):
        raise McpConfigError(
            f"MCP config at {config_path} must contain a JSON object at the top level."
        )

    servers_section = data.get(_TOP_LEVEL_KEY)
    if servers_section is None:
        return {}
    if not isinstance(servers_section, dict):
        raise McpConfigError(
            f"'{_TOP_LEVEL_KEY}' in {config_path} must be a JSON object "
            "mapping server names to their configuration."
        )

    return {name: _parse_server(name, entry) for name, entry in servers_section.items()}


def _parse_server(name: str, entry: Any) -> McpServer:
    """Validate one MCP server entry and return the corresponding ``McpServer``."""
    if not isinstance(entry, dict):
        raise McpConfigError(
            f"MCP server '/{name}' configuration must be a JSON object."
        )

    transport = entry.get("transport") or entry.get("type")
    if transport is not None and transport not in _ALLOWED_TRANSPORTS:
        raise McpConfigError(
            f"MCP server '/{name}' uses unsupported transport '{transport}'. "
            "v1 supports only command-based stdio servers."
        )

    command = entry.get("command")
    if not isinstance(command, str) or not command.strip():
        raise McpConfigError(
            f"MCP server '/{name}' is missing a non-empty 'command' string."
        )

    raw_args = entry.get("args", [])
    if not isinstance(raw_args, list) or not all(isinstance(a, str) for a in raw_args):
        raise McpConfigError(
            f"MCP server '/{name}' has invalid 'args': expected a list of strings."
        )

    raw_env = entry.get("env", {})
    if raw_env is None:
        raw_env = {}
    if not isinstance(raw_env, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in raw_env.items()
    ):
        raise McpConfigError(
            f"MCP server '/{name}' has invalid 'env': expected an object of "
            "string keys and string values."
        )

    return McpServer(
        name=name,
        command=command,
        args=tuple(raw_args),
        env=dict(raw_env),
    )
