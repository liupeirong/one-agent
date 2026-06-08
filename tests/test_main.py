"""Integration tests for the main entry point."""

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import main


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Provide valid config env vars, suppress .env loading, isolate skills dir."""
    monkeypatch.setattr("one_agent.config.load_dotenv", lambda: None)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")  # pragma: allowlist secret
    # Point ~/.claude/skills and ~/.claude.json at an isolated temp directory
    # so the test environment does not leak real user skills or MCP servers.
    fake_home = tmp_path / "home"
    (fake_home / ".claude" / "skills").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)


class TestMainEntryPoint:
    @patch("main.invoke", return_value="Hello from LLM")
    def test_prints_answer_to_stdout(
        self,
        _mock_invoke: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent", "Say hello"])

        main()

        captured = capsys.readouterr()
        assert captured.out.strip() == "Hello from LLM"
        assert captured.err == ""

    def test_cli_error_prints_to_stderr(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent"])
        fake_tty = io.StringIO()
        fake_tty.isatty = lambda: True  # type: ignore[assignment]
        monkeypatch.setattr("sys.stdin", fake_tty)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Usage" in captured.err

    @patch("main.invoke", return_value="answer")
    def test_config_error_prints_to_stderr(
        self,
        _mock_invoke: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent", "hello"])
        monkeypatch.delenv("OPENAI_BASE_URL")
        monkeypatch.delenv("OPENAI_MODEL")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "OPENAI_BASE_URL" in captured.err

    def test_unknown_mention_prints_to_stderr(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent", "@writer help"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "@writer" in captured.err

    def test_empty_task_after_mentions_prints_to_stderr(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent", "@writer"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "no task text" in captured.err

    @patch("main.invoke", side_effect=ConnectionError("network unreachable"))
    def test_unexpected_error_prints_to_stderr(
        self,
        _mock_invoke: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent", "hello"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "network unreachable" in captured.err

    @patch("main.invoke", return_value="answer")
    def test_known_skill_is_loaded_and_passed_as_system_instructions(
        self,
        mock_invoke: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        skill_dir = Path.home() / ".claude" / "skills" / "writer"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("Write clearly.", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["one-agent", "@writer draft a haiku"])

        main()

        _, kwargs = mock_invoke.call_args
        assert kwargs["prompt"] == "draft a haiku"
        assert kwargs["system_instructions"] is not None
        assert "Write clearly." in kwargs["system_instructions"]
        assert "@writer" in kwargs["system_instructions"]

    @patch("main.invoke", return_value="answer")
    def test_no_mention_passes_no_system_instructions(
        self,
        mock_invoke: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent", "plain prompt"])

        main()

        _, kwargs = mock_invoke.call_args
        assert kwargs["system_instructions"] is None
        assert kwargs["mcp_servers"] is None

    @patch("main.invoke", return_value="agent answer")
    def test_known_mcp_passes_selected_server(
        self,
        mock_invoke: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import json

        (Path.home() / ".claude.json").write_text(
            json.dumps(
                {"mcpServers": {"tavily": {"command": "npx", "args": ["-y", "x"]}}}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr("sys.argv", ["one-agent", "search /tavily for python"])

        main()

        _, kwargs = mock_invoke.call_args
        servers = kwargs["mcp_servers"]
        assert servers is not None
        assert [s.name for s in servers] == ["tavily"]
        assert kwargs["prompt"] == "search for python"

    def test_unknown_mcp_mention_prints_to_stderr(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["one-agent", "use /tavily please"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "/tavily" in captured.err

    def test_invalid_mcp_config_prints_to_stderr_when_mentioned(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (Path.home() / ".claude.json").write_text("{not json", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["one-agent", "use /tavily please"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err

    @patch("main.invoke", return_value="ok")
    def test_malformed_mcp_config_does_not_block_runs_without_mcp_mention(
        self,
        _mock_invoke: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        (Path.home() / ".claude.json").write_text("{not json", encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["one-agent", "plain prompt"])

        # Should not raise: ~/.claude.json belongs to the Claude CLI and is
        # only loaded when the user explicitly asks for an MCP server.
        main()
