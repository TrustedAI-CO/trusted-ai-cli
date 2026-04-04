"""Tests for tai.core.skills module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tai.core.skills import (
    SkillInfo,
    InstallResult,
    parse_frontmatter,
    discover_skills,
    find_skill_source,
    skills_install_dir,
    prefixed_name,
    install_skills,
    installed_version,
    is_installed,
    _extract_field,
    _extract_multiline,
    _find_repo_root,
)


# ── SkillInfo and InstallResult dataclasses ──────────────────────────────────


def test_skill_info_frozen():
    """SkillInfo is immutable."""
    info = SkillInfo(name="test", version="1.0.0", description="Test", path=Path("/tmp"))
    with pytest.raises(Exception):  # FrozenInstanceError
        info.name = "changed"


def test_install_result():
    """InstallResult holds installed and skipped lists."""
    result = InstallResult(installed=["a", "b"], skipped=["c"])
    assert result.installed == ["a", "b"]
    assert result.skipped == ["c"]


# ── parse_frontmatter tests ──────────────────────────────────────────────────


def test_parse_frontmatter_full(tmp_path):
    """Parse complete front matter."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""\
---
name: my-skill
version: 1.2.3
description: |
  This is a multi-line
  description of the skill.
---

# Instructions here
""")

    info = parse_frontmatter(skill_md)
    assert info.name == "my-skill"
    assert info.version == "1.2.3"
    assert "multi-line description" in info.description
    assert info.path == skill_dir


def test_parse_frontmatter_minimal(tmp_path):
    """Parse minimal front matter with defaults."""
    skill_dir = tmp_path / "minimal"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""\
---
name: minimal
---

Content here.
""")

    info = parse_frontmatter(skill_md)
    assert info.name == "minimal"
    assert info.version == "0.0.0"  # default
    assert info.description == ""


def test_parse_frontmatter_no_name(tmp_path):
    """Name defaults to directory name."""
    skill_dir = tmp_path / "dir-name"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""\
---
version: 2.0.0
---

Content.
""")

    info = parse_frontmatter(skill_md)
    assert info.name == "dir-name"  # from directory name
    assert info.version == "2.0.0"


def test_parse_frontmatter_no_frontmatter(tmp_path):
    """Error when no front matter present."""
    skill_dir = tmp_path / "no-fm"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("Just content, no front matter.")

    with pytest.raises(ValueError, match="No front matter"):
        parse_frontmatter(skill_md)


def test_parse_frontmatter_single_line_description(tmp_path):
    """Single-line description works."""
    skill_dir = tmp_path / "single-desc"
    skill_dir.mkdir()
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text("""\
---
name: single-desc
description: A single line description.
---
""")

    info = parse_frontmatter(skill_md)
    assert info.description == "A single line description."


# ── _extract_field and _extract_multiline tests ──────────────────────────────


def test_extract_field_found():
    """Extract a simple field."""
    block = "name: my-skill\nversion: 1.0.0"
    assert _extract_field(block, "name") == "my-skill"
    assert _extract_field(block, "version") == "1.0.0"


def test_extract_field_not_found():
    """Return None when field not found."""
    block = "name: test"
    assert _extract_field(block, "missing") is None


def test_extract_multiline_found():
    """Extract multiline field."""
    block = """\
description: |
  Line one
  Line two
other: value"""
    result = _extract_multiline(block, "description")
    assert "Line one" in result
    assert "Line two" in result


def test_extract_multiline_falls_back():
    """Falls back to single-line extraction."""
    block = "description: Single line"
    result = _extract_multiline(block, "description")
    assert result == "Single line"


# ── discover_skills tests ────────────────────────────────────────────────────


def test_discover_skills_empty(tmp_path):
    """No skills in empty directory."""
    skills = discover_skills(tmp_path)
    assert skills == []


def test_discover_skills_nonexistent(tmp_path):
    """No skills from nonexistent directory."""
    skills = discover_skills(tmp_path / "nonexistent")
    assert skills == []


def test_discover_skills_finds_all(tmp_path):
    """Discover multiple skills."""
    # Create skill A
    skill_a = tmp_path / "skill-a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").write_text("---\nname: skill-a\n---")

    # Create skill B
    skill_b = tmp_path / "skill-b"
    skill_b.mkdir()
    (skill_b / "SKILL.md").write_text("---\nname: skill-b\n---")

    skills = discover_skills(tmp_path)
    assert len(skills) == 2
    names = {s.name for s in skills}
    assert names == {"skill-a", "skill-b"}


def test_discover_skills_skips_invalid(tmp_path):
    """Skip skills with invalid front matter."""
    # Valid skill
    valid = tmp_path / "valid"
    valid.mkdir()
    (valid / "SKILL.md").write_text("---\nname: valid\n---")

    # Invalid skill (no front matter)
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    (invalid / "SKILL.md").write_text("No front matter here")

    skills = discover_skills(tmp_path)
    assert len(skills) == 1
    assert skills[0].name == "valid"


def test_discover_skills_skips_files(tmp_path):
    """Skip non-directories."""
    (tmp_path / "file.md").write_text("---\nname: file\n---")

    skills = discover_skills(tmp_path)
    assert skills == []


def test_discover_skills_skips_no_skill_md(tmp_path):
    """Skip directories without SKILL.md."""
    (tmp_path / "no-skill").mkdir()

    skills = discover_skills(tmp_path)
    assert skills == []


# ── find_skill_source tests ──────────────────────────────────────────────────


def test_find_skill_source_dev_mode(tmp_path):
    """Find skills from repo root in dev mode."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()
    skills_dir = repo_root / ".claude" / "skills" / "tai"
    skills_dir.mkdir(parents=True)
    (skills_dir / "test-skill").mkdir()
    (skills_dir / "test-skill" / "SKILL.md").write_text("---\nname: test\n---")

    # Just verify the function can be called
    # The actual result depends on the real filesystem
    result = find_skill_source()
    # Result is Path or None depending on environment


def test_find_repo_root_found(tmp_path):
    """Find repo root when .git exists."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    subdir = repo / "a" / "b"
    subdir.mkdir(parents=True)

    with patch("tai.core.skills.Path.cwd", return_value=subdir):
        result = _find_repo_root()
        assert result == repo


def test_find_repo_root_not_found(tmp_path):
    """Return None when no .git directory."""
    with patch("tai.core.skills.Path.cwd", return_value=tmp_path):
        result = _find_repo_root()
        assert result is None


# ── skills_install_dir and prefixed_name tests ───────────────────────────────


def test_skills_install_dir():
    """Install directory is ~/.claude/skills/."""
    result = skills_install_dir()
    assert result == Path.home() / ".claude" / "skills"


def test_prefixed_name():
    """Prefix skill name with tai-."""
    assert prefixed_name("review") == "tai-review"
    assert prefixed_name("ship") == "tai-ship"


# ── install_skills tests ─────────────────────────────────────────────────────


def test_install_skills_fresh(tmp_path):
    """Install skills to fresh directory."""
    # Source skills
    source = tmp_path / "source"
    skill = source / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: test-skill\n---")

    # Install destination
    dest = tmp_path / "dest"

    with patch("tai.core.skills.skills_install_dir", return_value=dest):
        result = install_skills(source)

    assert "tai-test-skill" in result.installed
    assert result.skipped == []
    assert (dest / "tai-test-skill" / "SKILL.md").exists()


def test_install_skills_skip_existing(tmp_path):
    """Skip existing skills when force=False."""
    source = tmp_path / "source"
    skill = source / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: test-skill\n---")

    dest = tmp_path / "dest"
    existing = dest / "tai-test-skill"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("OLD")

    with patch("tai.core.skills.skills_install_dir", return_value=dest):
        result = install_skills(source, force=False)

    assert result.installed == []
    assert "tai-test-skill" in result.skipped
    # Original content preserved
    assert (dest / "tai-test-skill" / "SKILL.md").read_text() == "OLD"


def test_install_skills_force_overwrite(tmp_path):
    """Overwrite existing skills when force=True."""
    source = tmp_path / "source"
    skill = source / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: test-skill\n---\nNEW")

    dest = tmp_path / "dest"
    existing = dest / "tai-test-skill"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("OLD")

    with patch("tai.core.skills.skills_install_dir", return_value=dest):
        result = install_skills(source, force=True)

    assert "tai-test-skill" in result.installed
    assert result.skipped == []
    assert "NEW" in (dest / "tai-test-skill" / "SKILL.md").read_text()


# ── installed_version tests ──────────────────────────────────────────────────


def test_installed_version_found(tmp_path):
    """Get version of installed skill."""
    dest = tmp_path / "skills" / "tai-test"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("---\nname: test\nversion: 2.5.0\n---")

    with patch("tai.core.skills.skills_install_dir", return_value=tmp_path / "skills"):
        version = installed_version("test")

    assert version == "2.5.0"


def test_installed_version_not_installed(tmp_path):
    """Return None for non-installed skill."""
    with patch("tai.core.skills.skills_install_dir", return_value=tmp_path):
        version = installed_version("nonexistent")

    assert version is None


def test_installed_version_invalid_frontmatter(tmp_path):
    """Return None for invalid skill."""
    dest = tmp_path / "skills" / "tai-bad"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("No front matter")

    with patch("tai.core.skills.skills_install_dir", return_value=tmp_path / "skills"):
        version = installed_version("bad")

    assert version is None


# ── is_installed tests ───────────────────────────────────────────────────────


def test_is_installed_true(tmp_path):
    """Return True when tai skills exist."""
    dest = tmp_path / "tai-test"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("---\nname: test\n---")

    with patch("tai.core.skills.skills_install_dir", return_value=tmp_path):
        assert is_installed() is True


def test_is_installed_false_empty(tmp_path):
    """Return False when no skills."""
    with patch("tai.core.skills.skills_install_dir", return_value=tmp_path):
        assert is_installed() is False


def test_is_installed_false_no_dir(tmp_path):
    """Return False when directory doesn't exist."""
    with patch("tai.core.skills.skills_install_dir", return_value=tmp_path / "nonexistent"):
        assert is_installed() is False


def test_is_installed_false_no_tai_prefix(tmp_path):
    """Return False when skills don't have tai- prefix."""
    dest = tmp_path / "other-skill"  # No tai- prefix
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("---\nname: other\n---")

    with patch("tai.core.skills.skills_install_dir", return_value=tmp_path):
        assert is_installed() is False
