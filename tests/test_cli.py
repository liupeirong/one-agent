"""Unit tests for one_agent.cli."""

import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.cli import CliError, parse_prompt


def _tty_stdin() -> io.StringIO:
    """Return a StringIO that reports isatty() == True."""
    s = io.StringIO()
    s.isatty = lambda: True  # type: ignore[assignment]
    return s


class TestParsePromptFromArg:
    def test_returns_prompt_from_single_arg(self) -> None:
        assert parse_prompt(["Explain this task"]) == "Explain this task"

    def test_strips_whitespace(self) -> None:
        assert parse_prompt(["  hello world  "]) == "hello world"

    def test_fails_on_multiple_args(self) -> None:
        with pytest.raises(CliError, match="single prompt"):
            parse_prompt(["arg1", "arg2"])

    def test_fails_on_blank_prompt(self) -> None:
        with pytest.raises(CliError, match="blank"):
            parse_prompt(["   "])

    def test_fails_on_empty_string(self) -> None:
        with pytest.raises(CliError, match="blank"):
            parse_prompt([""])


class TestParsePromptFromStdin:
    def test_reads_from_piped_stdin(self) -> None:
        result = parse_prompt([], stdin=io.StringIO("hello from pipe"))
        assert result == "hello from pipe"

    def test_reads_multiline_from_stdin(self) -> None:
        result = parse_prompt([], stdin=io.StringIO("line one\nline two\nline three"))
        assert result == "line one\nline two\nline three"

    def test_strips_surrounding_whitespace(self) -> None:
        result = parse_prompt([], stdin=io.StringIO("  hello  \n"))
        assert result == "hello"

    def test_fails_on_blank_stdin(self) -> None:
        with pytest.raises(CliError, match="blank"):
            parse_prompt([], stdin=io.StringIO("   \n  "))

    def test_fails_on_tty_stdin_with_no_args(self) -> None:
        with pytest.raises(CliError, match="Usage"):
            parse_prompt([], stdin=_tty_stdin())

    def test_arg_takes_precedence_over_stdin(self) -> None:
        result = parse_prompt(["from arg"], stdin=io.StringIO("from stdin"))
        assert result == "from arg"


class TestParsePromptFromFile:
    def test_reads_prompt_from_file(self, tmp_path: Path) -> None:
        f = tmp_path / "prompt.txt"
        f.write_text("hello from file", encoding="utf-8")

        result = parse_prompt(["--file", str(f)])
        assert result == "hello from file"

    def test_reads_multiline_file(self, tmp_path: Path) -> None:
        f = tmp_path / "prompt.txt"
        f.write_text("line one\nline two\nline three", encoding="utf-8")

        result = parse_prompt(["--file", str(f)])
        assert result == "line one\nline two\nline three"

    def test_strips_whitespace_from_file(self, tmp_path: Path) -> None:
        f = tmp_path / "prompt.txt"
        f.write_text("  hello  \n\n", encoding="utf-8")

        result = parse_prompt(["--file", str(f)])
        assert result == "hello"

    def test_fails_on_blank_file(self, tmp_path: Path) -> None:
        f = tmp_path / "prompt.txt"
        f.write_text("   \n  ", encoding="utf-8")

        with pytest.raises(CliError, match="blank"):
            parse_prompt(["--file", str(f)])

    def test_fails_on_missing_file(self) -> None:
        with pytest.raises(CliError, match="not found"):
            parse_prompt(["--file", "nonexistent.txt"])

    def test_fails_when_file_path_missing(self) -> None:
        with pytest.raises(CliError, match="requires a file path"):
            parse_prompt(["--file"])

    def test_fails_when_combined_with_positional(self, tmp_path: Path) -> None:
        f = tmp_path / "prompt.txt"
        f.write_text("hello", encoding="utf-8")

        with pytest.raises(CliError, match="cannot be combined"):
            parse_prompt(["some prompt", "--file", str(f)])
