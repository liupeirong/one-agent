"""Tests for routing mention parsing and validation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.mentions import (
    MentionError,
    ParsedPrompt,
    parse_mentions,
    validate_mentions,
)


class TestParseMentions:
    def test_no_mentions_returns_prompt_unchanged(self) -> None:
        result = parse_mentions("just a plain prompt")
        assert result == ParsedPrompt(task="just a plain prompt", skills=(), mcps=())

    def test_single_skill_mention_at_start(self) -> None:
        result = parse_mentions("@writer draft a poem")
        assert result.skills == ("writer",)
        assert result.mcps == ()
        assert result.task == "draft a poem"

    def test_single_mcp_mention_anywhere(self) -> None:
        result = parse_mentions("search the web with /tavily please")
        assert result.mcps == ("tavily",)
        assert result.skills == ()
        assert result.task == "search the web with please"

    def test_multiple_mentions_preserve_order(self) -> None:
        result = parse_mentions("@writer use /tavily then @editor polish it")
        assert result.skills == ("writer", "editor")
        assert result.mcps == ("tavily",)
        assert result.task == "use then polish it"

    def test_duplicate_mentions_deduplicated(self) -> None:
        result = parse_mentions("@writer think @writer again")
        assert result.skills == ("writer",)
        assert result.task == "think again"

    def test_names_allow_letters_numbers_underscore_hyphen(self) -> None:
        result = parse_mentions("@writer_v2 and @code-gen3 with /mcp-server_1")
        assert result.skills == ("writer_v2", "code-gen3")
        assert result.mcps == ("mcp-server_1",)

    def test_email_at_sign_does_not_trigger_skill(self) -> None:
        result = parse_mentions("email user@example.com about it")
        assert result.skills == ()
        assert result.task == "email user@example.com about it"

    def test_path_slash_does_not_trigger_mcp(self) -> None:
        result = parse_mentions("read /etc/hosts and /var/log/syslog")
        assert result.mcps == ()
        assert "/etc/hosts" in result.task
        assert "/var/log/syslog" in result.task

    def test_mcp_mention_not_matched_inside_path(self) -> None:
        result = parse_mentions("look at path/to/foo not a server")
        assert result.mcps == ()

    def test_whitespace_collapsed_after_stripping(self) -> None:
        result = parse_mentions("hello    @writer   world")
        assert result.task == "hello world"

    def test_trailing_punctuation_allowed_after_mention(self) -> None:
        result = parse_mentions("please @writer, do this")
        assert result.skills == ("writer",)
        assert result.task == "please, do this"

    def test_quoted_mention_recognised(self) -> None:
        result = parse_mentions('use "@writer" to draft')
        assert result.skills == ("writer",)
        assert "writer" not in result.task

    def test_mention_only_prompt_yields_empty_task(self) -> None:
        result = parse_mentions("@writer /tavily")
        assert result.task == ""
        assert result.skills == ("writer",)
        assert result.mcps == ("tavily",)


class TestValidateMentions:
    def test_empty_task_raises(self) -> None:
        parsed = ParsedPrompt(task="", skills=("writer",), mcps=())
        with pytest.raises(MentionError, match="no task text"):
            validate_mentions(parsed, known_skills=("writer",), known_mcps=())

    def test_unknown_skill_raises_with_name(self) -> None:
        parsed = ParsedPrompt(task="hi", skills=("writer",), mcps=())
        with pytest.raises(MentionError, match="@writer"):
            validate_mentions(parsed, known_skills=("editor",), known_mcps=())

    def test_unknown_mcp_raises_with_name(self) -> None:
        parsed = ParsedPrompt(task="hi", skills=(), mcps=("tavily",))
        with pytest.raises(MentionError, match="/tavily"):
            validate_mentions(parsed, known_skills=(), known_mcps=("other",))

    def test_all_known_passes(self) -> None:
        parsed = ParsedPrompt(task="hi", skills=("writer",), mcps=("tavily",))
        validate_mentions(
            parsed, known_skills=("writer", "editor"), known_mcps=("tavily",)
        )

    def test_no_mentions_passes_with_empty_known_sets(self) -> None:
        parsed = ParsedPrompt(task="hi", skills=(), mcps=())
        validate_mentions(parsed, known_skills=(), known_mcps=())
