"""Tests for tai codex commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from tai.commands.codex import app
from tai.core.context import AppContext

runner = CliRunner()


def _skill_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    skill = source / "review"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: review\nversion: 1.0.0\n---\n")
    return source


def test_status_json_reports_codex_state(tmp_path):
    codex_home = tmp_path / ".codex"
    skills_dir = codex_home / "skills"
    (skills_dir / "tai-review").mkdir(parents=True)
    (skills_dir / "tai-review" / "SKILL.md").write_text("---\nname: review\n---")
    agents = tmp_path / "repo" / "AGENTS.md"
    agents.parent.mkdir()
    agents.write_text("# Repository Guidelines\n")

    ctx = AppContext(json_output=True)
    with (
        patch("shutil.which", return_value="/usr/local/bin/codex"),
        patch("tai.commands.codex.codex_home", return_value=codex_home),
        patch("tai.commands.codex.skills_install_dir", return_value=skills_dir),
        patch("tai.commands.codex.Path.cwd", return_value=agents.parent),
    ):
        result = runner.invoke(app, ["status"], obj=ctx)

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["binary"] == "/usr/local/bin/codex"
    assert data["installed"] is True
    assert data["skills_installed"] == 1
    assert data["agents_md_exists"] is True


def test_setup_skills_installs_to_codex_dir(tmp_path):
    source = _skill_source(tmp_path)
    dest = tmp_path / ".codex" / "skills"
    ctx = AppContext(json_output=True)

    with (
        patch("tai.commands.codex.find_skill_source", return_value=source),
        patch("tai.commands.codex.skills_install_dir", return_value=dest),
        patch("tai.core.skills.skills_install_dir", return_value=dest),
    ):
        result = runner.invoke(app, ["setup-skills", "--json"], obj=ctx)

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["install_path"] == str(dest)
    assert data["installed"] == ["tai-review"]
    assert (dest / "tai-review" / "SKILL.md").exists()


def test_setup_skills_is_idempotent_without_force(tmp_path):
    source = _skill_source(tmp_path)
    dest = tmp_path / ".codex" / "skills"
    existing = dest / "tai-review"
    existing.mkdir(parents=True)
    (existing / "SKILL.md").write_text("OLD")

    with (
        patch("tai.commands.codex.find_skill_source", return_value=source),
        patch("tai.commands.codex.skills_install_dir", return_value=dest),
        patch("tai.core.skills.skills_install_dir", return_value=dest),
    ):
        result = runner.invoke(app, ["setup-skills"])

    assert result.exit_code == 0
    assert "skipped" in result.output
    assert (existing / "SKILL.md").read_text() == "OLD"


def test_setup_agents_creates_managed_agents_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    result = runner.invoke(app, ["setup-agents", "--path", str(repo), "--json"])

    assert result.exit_code == 0
    agents = repo / "AGENTS.md"
    assert agents.exists()
    text = agents.read_text()
    assert "Repository Guidelines" in text
    assert "tai codex setup-skills" in text
    assert "tai:codex-agents-template" in text
    data = json.loads(result.output)
    assert data["path"] == str(agents)
    assert data["written"] is True


def test_setup_agents_refuses_unmanaged_overwrite(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    agents = repo / "AGENTS.md"
    agents.write_text("# Custom guide\n")

    result = runner.invoke(app, ["setup-agents", "--path", str(repo)])

    assert result.exit_code == 5
    assert "AGENTS.md already exists" in result.output
    assert agents.read_text() == "# Custom guide\n"


def test_setup_agents_force_overwrites_unmanaged_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    agents = repo / "AGENTS.md"
    agents.write_text("# Custom guide\n")

    result = runner.invoke(app, ["setup-agents", "--path", str(repo), "--force"])

    assert result.exit_code == 0
    assert "Updated" in result.output
    assert "tai:codex-agents-template" in agents.read_text()
