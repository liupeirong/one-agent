"""Unit tests for one_agent.cli."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.cli import CliError, parse_prompt


class TestParsePrompt:
    def test_returns_prompt_from_single_arg(self) -> None:
        assert parse_prompt(["Explain this task"]) == "Explain this task"

    def test_strips_whitespace(self) -> None:
        assert parse_prompt(["  hello world  "]) == "hello world"

    def test_fails_on_no_args(self) -> None:
        with pytest.raises(CliError, match="Usage"):
            parse_prompt([])

    def test_fails_on_multiple_args(self) -> None:
        with pytest.raises(CliError, match="single prompt"):
            parse_prompt(["arg1", "arg2"])

    def test_fails_on_blank_prompt(self) -> None:
        with pytest.raises(CliError, match="blank"):
            parse_prompt(["   "])

    def test_fails_on_empty_string(self) -> None:
        with pytest.raises(CliError, match="blank"):
            parse_prompt([""])
