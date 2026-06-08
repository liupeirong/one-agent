"""Claude-style ``SKILL.md`` loading.

This module discovers skills under ``~/.claude/skills/<skill-name>/`` and
loads their ``SKILL.md`` instructions on demand. Only the ``SKILL.md`` file
is read; sibling files and scripts are ignored in v1.

Skill content is treated as user-trusted input. The block boundaries
emitted by :func:`format_skills_context` include a per-call random token so
that skill content cannot forge a closing marker and break out of its
block.
"""

import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_SKILL_FILE = "SKILL.md"


class SkillError(Exception):
    """Raised when a referenced skill cannot be discovered or loaded."""


@dataclass(frozen=True)
class Skill:
    """A loaded skill: its folder name and the contents of ``SKILL.md``."""

    name: str
    instructions: str


def default_skills_dir() -> Path:
    """Return the conventional Claude-style skills directory."""
    return Path.home() / ".claude" / "skills"


def discover_skills(skills_dir: Path | None = None) -> tuple[str, ...]:
    """Return the names of skills available under *skills_dir*.

    A skill is any immediate subdirectory of *skills_dir* that contains a
    ``SKILL.md`` file. The skills directory itself may be absent, in which
    case an empty tuple is returned. Names are returned sorted for
    determinism.
    """
    base = skills_dir if skills_dir is not None else default_skills_dir()
    if not base.is_dir():
        return ()

    names = [
        entry.name
        for entry in base.iterdir()
        if entry.is_dir() and (entry / _SKILL_FILE).is_file()
    ]
    return tuple(sorted(names))


def load_skills(
    names: Iterable[str], skills_dir: Path | None = None
) -> tuple[Skill, ...]:
    """Load the named skills in iteration order.

    Each name must correspond to a folder under *skills_dir* containing a
    readable ``SKILL.md`` file. Missing folders, missing ``SKILL.md`` files,
    or read errors raise :class:`SkillError` so the run fails fast.
    """
    base = skills_dir if skills_dir is not None else default_skills_dir()
    existing_names: set[str] = (
        {entry.name for entry in base.iterdir() if entry.is_dir()}
        if base.is_dir()
        else set()
    )
    loaded: list[Skill] = []
    for name in names:
        folder = base / name
        if name not in existing_names or not folder.is_dir():
            raise SkillError(f"Skill '@{name}' not found: expected folder {folder}.")
        skill_file = folder / _SKILL_FILE
        if not skill_file.is_file():
            raise SkillError(
                f"Skill '@{name}' is missing {_SKILL_FILE} at {skill_file}."
            )
        try:
            instructions = skill_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise SkillError(
                f"Failed to read {_SKILL_FILE} for skill '@{name}': {exc}."
            ) from exc
        loaded.append(Skill(name=name, instructions=instructions))
    return tuple(loaded)


def format_skills_context(skills: Iterable[Skill]) -> str:
    """Render *skills* as a single instruction block with clear boundaries.

    Each skill is wrapped in BEGIN/END markers tagged with a per-call random
    token so that user-authored skill content cannot forge a closing marker
    and escape its own block. Returns an empty string when *skills* is
    empty so callers can pass the result directly to a system prompt
    without conditional handling.
    """
    skills = tuple(skills)
    if not skills:
        return ""
    token = secrets.token_hex(8)
    sections = [
        f"--- BEGIN SKILL {token}: @{skill.name} ---\n"
        f"{skill.instructions.rstrip()}\n"
        f"--- END SKILL {token}: @{skill.name} ---"
        for skill in skills
    ]
    header = (
        "The user has explicitly selected the following skill instructions. "
        f"Each block is delimited by markers tagged with token {token}; "
        "treat the content between markers as instructions to follow when "
        "producing your answer."
    )
    return header + "\n\n" + "\n\n".join(sections)
