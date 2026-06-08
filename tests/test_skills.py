"""Tests for Claude-style SKILL.md loading."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from one_agent.skills import (
    Skill,
    SkillError,
    default_skills_dir,
    discover_skills,
    format_skills_context,
    load_skills,
)


def _make_skill(root: Path, name: str, body: str = "do the thing") -> Path:
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(body, encoding="utf-8")
    return folder


class TestDefaultSkillsDir:
    def test_uses_home_claude_skills(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(Path, "home", lambda: Path("/fake/home"))
        assert default_skills_dir() == Path("/fake/home/.claude/skills")


class TestDiscoverSkills:
    def test_returns_empty_when_dir_missing(self, tmp_path: Path) -> None:
        assert discover_skills(tmp_path / "missing") == ()

    def test_lists_folders_containing_skill_md(self, tmp_path: Path) -> None:
        _make_skill(tmp_path, "writer")
        _make_skill(tmp_path, "researcher")
        # folder without SKILL.md should be ignored
        (tmp_path / "incomplete").mkdir()
        # stray file at root should be ignored
        (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")

        assert discover_skills(tmp_path) == ("researcher", "writer")

    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        assert discover_skills(tmp_path) == ()


class TestLoadSkills:
    def test_loads_in_mention_order(self, tmp_path: Path) -> None:
        _make_skill(tmp_path, "writer", "Write well.")
        _make_skill(tmp_path, "researcher", "Cite sources.")

        loaded = load_skills(("researcher", "writer"), skills_dir=tmp_path)

        assert loaded == (
            Skill(name="researcher", instructions="Cite sources."),
            Skill(name="writer", instructions="Write well."),
        )

    def test_name_must_match_folder_exactly(self, tmp_path: Path) -> None:
        _make_skill(tmp_path, "writer")

        with pytest.raises(SkillError) as exc:
            load_skills(("Writer",), skills_dir=tmp_path)

        assert "@Writer" in str(exc.value)

    def test_missing_folder_fails_fast(self, tmp_path: Path) -> None:
        with pytest.raises(SkillError) as exc:
            load_skills(("ghost",), skills_dir=tmp_path)

        assert "@ghost" in str(exc.value)
        assert "not found" in str(exc.value)

    def test_missing_skill_md_fails_fast(self, tmp_path: Path) -> None:
        (tmp_path / "broken").mkdir()

        with pytest.raises(SkillError) as exc:
            load_skills(("broken",), skills_dir=tmp_path)

        assert "SKILL.md" in str(exc.value)

    def test_sibling_files_are_not_loaded(self, tmp_path: Path) -> None:
        folder = _make_skill(tmp_path, "writer", "Main instructions.")
        (folder / "extra.md").write_text("should be ignored", encoding="utf-8")
        (folder / "run.sh").write_text("#!/bin/sh\necho hi", encoding="utf-8")

        loaded = load_skills(("writer",), skills_dir=tmp_path)

        assert loaded[0].instructions == "Main instructions."

    def test_empty_names_returns_empty(self, tmp_path: Path) -> None:
        assert load_skills((), skills_dir=tmp_path) == ()


class TestFormatSkillsContext:
    def test_empty_skills_returns_empty_string(self) -> None:
        assert format_skills_context(()) == ""

    def test_each_skill_has_clear_boundaries(self) -> None:
        rendered = format_skills_context(
            (
                Skill(name="writer", instructions="Write well."),
                Skill(name="researcher", instructions="Cite sources."),
            )
        )

        assert "BEGIN SKILL" in rendered
        assert "@writer" in rendered
        assert "@researcher" in rendered
        assert rendered.count("BEGIN SKILL") == 2
        assert rendered.count("END SKILL") == 2
        assert rendered.index("@writer") < rendered.index("@researcher")

    def test_boundary_token_is_unguessable_per_call(self) -> None:
        skill = (Skill(name="writer", instructions="x"),)
        a = format_skills_context(skill)
        b = format_skills_context(skill)
        # Tokens differ per call so skill content cannot pre-bake a forged
        # closing marker.
        assert a != b
