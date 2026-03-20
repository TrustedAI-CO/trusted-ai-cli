"""Skill discovery, parsing, and installation to ~/.claude/skills/tai-<name>/."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

SKILL_PREFIX = "tai"


@dataclass(frozen=True)
class SkillInfo:
    name: str
    version: str
    description: str
    path: Path


@dataclass(frozen=True)
class InstallResult:
    installed: list[str]
    skipped: list[str]


def parse_frontmatter(skill_md: Path) -> SkillInfo:
    """Parse YAML front matter from a SKILL.md file."""
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError(f"No front matter in {skill_md}")

    block = match.group(1)
    name = _extract_field(block, "name") or skill_md.parent.name
    version = _extract_field(block, "version") or "0.0.0"
    description = _extract_multiline(block, "description") or ""
    return SkillInfo(
        name=name,
        version=version,
        description=description.strip(),
        path=skill_md.parent,
    )


def _extract_field(block: str, key: str) -> str | None:
    match = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_multiline(block: str, key: str) -> str | None:
    match = re.search(rf"^{key}:\s*\|\s*\n((?:\s+.+\n?)+)", block, re.MULTILINE)
    if match:
        lines = match.group(1).splitlines()
        return " ".join(line.strip() for line in lines if line.strip())
    return _extract_field(block, key)


def discover_skills(source_dir: Path) -> list[SkillInfo]:
    """Find all skills (subdirectories with SKILL.md) in source_dir."""
    skills: list[SkillInfo] = []
    if not source_dir.is_dir():
        return skills
    for child in sorted(source_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.is_file():
            try:
                skills.append(parse_frontmatter(skill_md))
            except ValueError:
                continue
    return skills


def find_skill_source() -> Path | None:
    """Locate bundled skills: try package-relative path, importlib, then repo root."""
    # 1. Resolve relative to the tai package directory (works for pip/uv-tool installs)
    tai_pkg_dir = Path(__file__).resolve().parent.parent  # tai/core/skills.py -> tai/
    candidate = tai_pkg_dir / "data" / "skills"
    if candidate.is_dir() and any(candidate.iterdir()):
        return candidate

    # 2. Try importlib.resources
    try:
        from importlib.resources import files
        pkg_path = files("tai.data.skills")
        resolved = Path(str(pkg_path))
        if resolved.is_dir() and any(resolved.iterdir()):
            return resolved
    except (ImportError, ModuleNotFoundError, TypeError):
        pass

    # 3. Fall back to git repo root (dev mode — skills live in .claude/skills/tai/)
    repo_root = _find_repo_root()
    if repo_root:
        candidate = repo_root / ".claude" / "skills" / "tai"
        if candidate.is_dir():
            return candidate
    return None


def _find_repo_root() -> Path | None:
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def skills_install_dir() -> Path:
    """Base directory for personal skills: ~/.claude/skills/."""
    return Path.home() / ".claude" / "skills"


def prefixed_name(skill_name: str) -> str:
    """Return the tai-prefixed directory name for a skill."""
    return f"{SKILL_PREFIX}-{skill_name}"


def install_skills(source_dir: Path, *, force: bool = False) -> InstallResult:
    """Install skills to ~/.claude/skills/tai-<name>/.

    Each skill gets its own top-level directory so Claude Code
    discovers them as personal skills (e.g. tai-review, tai-ship).

    When force=True, existing skills are overwritten.
    """
    base = skills_install_dir()
    base.mkdir(parents=True, exist_ok=True)

    skills = discover_skills(source_dir)
    installed: list[str] = []
    skipped: list[str] = []

    for skill in skills:
        dest_name = prefixed_name(skill.name)
        dest = base / dest_name

        if dest.exists() and not force:
            skipped.append(dest_name)
            continue

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill.path, dest)
        installed.append(dest_name)

    return InstallResult(installed=installed, skipped=skipped)


def installed_version(skill_name: str) -> str | None:
    """Read the version of an installed skill, or None if not installed."""
    skill_md = skills_install_dir() / prefixed_name(skill_name) / "SKILL.md"
    if not skill_md.is_file():
        return None
    try:
        info = parse_frontmatter(skill_md)
        return info.version
    except ValueError:
        return None


def is_installed() -> bool:
    """Check if any tai skills are installed."""
    base = skills_install_dir()
    if not base.is_dir():
        return False
    return any(
        (base / d / "SKILL.md").is_file()
        for d in base.iterdir()
        if d.is_dir() and d.name.startswith(f"{SKILL_PREFIX}-")
    )
