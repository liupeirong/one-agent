"""Parse and validate ``@skill`` and ``/mcp`` mentions in user prompts.

This module is responsible only for prompt routing syntax. It does not load
skills or start MCP servers; those concerns belong to the skill and MCP
loader modules.
"""

import re
from dataclasses import dataclass
from typing import Iterable

_NAME = r"[A-Za-z0-9_-]+"

# A skill mention is ``@name`` not preceded by a word character or another
# ``@``. This excludes embedded ``@`` such as in ``user@example.com`` while
# still allowing quoted or bracketed mentions like ``"@writer"`` or
# ``(@writer)``.
_SKILL_RE = re.compile(rf"(?<![\w@])@({_NAME})(?![\w@])")

# An MCP mention is ``/name`` not preceded by a word character or ``/`` and
# not followed by another ``/``. This excludes path-like strings such as
# ``/etc/hosts`` or ``path/to/foo`` while allowing ``"/tavily"`` etc.
_MCP_RE = re.compile(rf"(?<![\w/])/({_NAME})(?![\w/])")


class MentionError(Exception):
    """Raised when a prompt contains an invalid or unknown mention."""


@dataclass(frozen=True)
class ParsedPrompt:
    """Result of parsing routing mentions from a user prompt."""

    task: str
    skills: tuple[str, ...]
    mcps: tuple[str, ...]


def parse_mentions(prompt: str) -> ParsedPrompt:
    """Extract ``@skill`` and ``/mcp`` mentions and strip them from *prompt*.

    Mentions are recognised anywhere in the prompt as long as they are not
    embedded in another token (for example ``user@example.com`` or a path
    like ``/etc/hosts``). Names may contain letters, numbers, ``_``, and
    ``-``. Each unique mention is preserved in first-appearance order.

    The returned :class:`ParsedPrompt` carries the task text with all
    matched mentions removed and surrounding whitespace collapsed.
    """
    skills = _unique([m.group(1) for m in _SKILL_RE.finditer(prompt)])
    mcps = _unique([m.group(1) for m in _MCP_RE.finditer(prompt)])

    stripped = _SKILL_RE.sub("", prompt)
    stripped = _MCP_RE.sub("", stripped)
    # Remove whitespace left in front of trailing punctuation (e.g. "please , do").
    stripped = re.sub(r"\s+([,.;:!?])", r"\1", stripped)
    task = re.sub(r"\s+", " ", stripped).strip()

    return ParsedPrompt(task=task, skills=skills, mcps=mcps)


def validate_mentions(
    parsed: ParsedPrompt,
    *,
    known_skills: Iterable[str],
    known_mcps: Iterable[str],
) -> None:
    """Fail fast if *parsed* references unknown skills or MCP servers.

    Also fails when the task text is empty after stripping mentions, since
    the agent has nothing to act on.
    """
    if not parsed.task:
        raise MentionError(
            "Prompt contains only routing mentions; no task text remains for the agent."
        )

    skill_set = set(known_skills)
    mcp_set = set(known_mcps)

    unknown_skills = [s for s in parsed.skills if s not in skill_set]
    if unknown_skills:
        lowered = {s.lower(): s for s in skill_set}
        parts: list[str] = []
        for name in unknown_skills:
            canonical = lowered.get(name.lower())
            if canonical and canonical != name:
                parts.append(f"@{name} (did you mean @{canonical}?)")
            else:
                parts.append(f"@{name}")
        raise MentionError(
            f"Unknown skill mention(s): {', '.join(parts)}. "
            "Ensure a matching folder exists under ~/.claude/skills/."
        )

    unknown_mcps = [m for m in parsed.mcps if m not in mcp_set]
    if unknown_mcps:
        raise MentionError(
            f"Unknown MCP mention(s): {', '.join('/' + m for m in unknown_mcps)}. "
            "Ensure the server is defined under mcpServers in ~/.claude.json."
        )


def _unique(values: list[str]) -> tuple[str, ...]:
    """Return *values* with duplicates removed, preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
