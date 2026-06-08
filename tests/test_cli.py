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
