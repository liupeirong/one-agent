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
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide valid config env vars and suppress .env loading."""
    monkeypatch.setattr("one_agent.config.load_dotenv", lambda: None)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")  # pragma: allowlist secret


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
