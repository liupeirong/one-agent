"""Tests for ~/.claude.json MCP server configuration loading."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.mcp_config import (
    McpConfigError,
    McpServer,
    default_mcp_config_path,
    load_mcp_config,
)


def _write_config(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / ".claude.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestDefaultMcpConfigPath:
    def test_uses_home_claude_json(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", lambda: Path("/fake/home"))
        assert default_mcp_config_path() == Path("/fake/home/.claude.json")


class TestLoadMcpConfig:
    def test_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        assert load_mcp_config(tmp_path / "absent.json") == {}

    def test_returns_empty_when_mcp_servers_absent(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, {"other": "stuff"})
        assert load_mcp_config(path) == {}

    def test_parses_single_stdio_server(self, tmp_path: Path) -> None:
        path = _write_config(
            tmp_path,
            {
                "mcpServers": {
                    "tavily": {
                        "command": "npx",
                        "args": ["-y", "tavily-mcp"],
                        "env": {"TAVILY_API_KEY": "secret"},  # pragma: allowlist secret
                    }
                }
            },
        )

        servers = load_mcp_config(path)

        assert servers == {
            "tavily": McpServer(
                name="tavily",
                command="npx",
                args=("-y", "tavily-mcp"),
                env={"TAVILY_API_KEY": "secret"},  # pragma: allowlist secret
            )
        }

    def test_defaults_args_and_env(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, {"mcpServers": {"plain": {"command": "do-it"}}})

        servers = load_mcp_config(path)

        assert servers["plain"].args == ()
        assert servers["plain"].env == {}

    def test_accepts_explicit_stdio_transport(self, tmp_path: Path) -> None:
        path = _write_config(
            tmp_path,
            {
                "mcpServers": {
                    "x": {"command": "run", "transport": "stdio"},
                    "y": {"command": "run", "type": "stdio"},
                }
            },
        )

        servers = load_mcp_config(path)

        assert set(servers) == {"x", "y"}

    def test_rejects_non_stdio_transport(self, tmp_path: Path) -> None:
        path = _write_config(
            tmp_path,
            {"mcpServers": {"web": {"command": "run", "transport": "sse"}}},
        )

        with pytest.raises(McpConfigError, match="unsupported transport 'sse'"):
            load_mcp_config(path)

    def test_missing_command_fails(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, {"mcpServers": {"bad": {"args": []}}})

        with pytest.raises(McpConfigError, match="/bad.*command"):
            load_mcp_config(path)

    def test_blank_command_fails(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, {"mcpServers": {"bad": {"command": "   "}}})

        with pytest.raises(McpConfigError, match="/bad.*command"):
            load_mcp_config(path)

    def test_invalid_args_fails(self, tmp_path: Path) -> None:
        path = _write_config(
            tmp_path,
            {"mcpServers": {"bad": {"command": "run", "args": [1, 2]}}},
        )

        with pytest.raises(McpConfigError, match="/bad.*args"):
            load_mcp_config(path)

    def test_invalid_env_fails(self, tmp_path: Path) -> None:
        path = _write_config(
            tmp_path,
            {"mcpServers": {"bad": {"command": "run", "env": {"k": 1}}}},
        )

        with pytest.raises(McpConfigError, match="/bad.*env"):
            load_mcp_config(path)

    def test_non_object_entry_fails(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, {"mcpServers": {"bad": "not-an-object"}})

        with pytest.raises(McpConfigError, match="/bad.*JSON object"):
            load_mcp_config(path)

    def test_mcp_servers_not_object_fails(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, {"mcpServers": ["nope"]})

        with pytest.raises(McpConfigError, match="must be a JSON object"):
            load_mcp_config(path)

    def test_top_level_not_object_fails(self, tmp_path: Path) -> None:
        path = tmp_path / ".claude.json"
        path.write_text("[]", encoding="utf-8")

        with pytest.raises(McpConfigError, match="JSON object at the top level"):
            load_mcp_config(path)

    def test_invalid_json_fails(self, tmp_path: Path) -> None:
        path = tmp_path / ".claude.json"
        path.write_text("{not json", encoding="utf-8")

        with pytest.raises(McpConfigError, match="Invalid JSON"):
            load_mcp_config(path)
