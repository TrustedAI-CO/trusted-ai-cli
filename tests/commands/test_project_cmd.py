"""Tests for tai project commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from tai.commands.project import app as project_app
from tai.main import app as main_app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig

runner = CliRunner()

PROJECT_RESPONSE = {
    "notion_url": "https://www.notion.so/2ef55eff03158039b95cf6e8ff60d632",
    "name": "Video Research",
    "status": "In progress",
    "phase": "POC",
    "github_repo": "https://github.com/TrustedAI-CO/video-research-poc",
    "drive_folder": "https://drive.google.com/drive/folders/1bHh28",
    "gchat_space": "spaces/ABC123",
    "description": None,
}

PROJECTS_LIST = [
    {"notion_page_id": "2ef55eff03158039b95cf6e8ff60d632", "notion_url": "https://www.notion.so/2ef55eff03158039b95cf6e8ff60d632", "name": "Video Research", "client": "Acme Corp", "status": "In progress", "phase": "POC"},
    {"notion_page_id": "29255eff031580779115e0a409355b98", "notion_url": "https://www.notion.so/29255eff031580779115e0a409355b98", "name": "SafeChat Improvement", "client": None, "status": "In progress", "phase": "Production"},
]


def _ctx(tmp_path: Path) -> AppContext:
    cfg = TaiConfig(profiles={"default": ProfileConfig(api_base_url="http://api.test")})
    return AppContext(profile="default", config=cfg)


def _mock_client(response_data: dict, status: int = 200) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.json.return_value = response_data
    client = MagicMock()
    client.get.return_value = resp
    client.patch.return_value = resp
    return client


# ── tai project status ────────────────────────────────────────────────────────


def test_status_shows_project_info(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    with (
        patch("tai.commands.project.find_repo_root", return_value=tmp_path),
        patch("tai.commands.project.build_client", return_value=_mock_client(PROJECT_RESPONSE)),
    ):
        result = runner.invoke(project_app, ["status"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Video Research" in result.output
    assert "In progress" in result.output
    assert "github.com/TrustedAI-CO" in result.output


def test_status_no_manifest(tmp_path):
    with patch("tai.commands.project.find_repo_root", return_value=tmp_path):
        result = runner.invoke(project_app, ["status"], obj=_ctx(tmp_path))

    assert result.exit_code == 1
    assert "not linked" in result.output.lower()


def test_status_outside_git_repo():
    with patch("tai.commands.project.find_repo_root", return_value=None):
        result = runner.invoke(project_app, ["status"], obj=_ctx(Path("/tmp")))

    assert result.exit_code == 1
    assert "git" in result.output.lower()



# ── tai link ──────────────────────────────────────────────────────────────────


def test_link_interactive_picker(tmp_path):
    list_client = _mock_client(PROJECTS_LIST)
    list_client.get.return_value.json.return_value = PROJECTS_LIST

    with (
        patch("tai.commands.project.find_repo_root", return_value=tmp_path),
        patch("tai.commands.project.build_client", return_value=list_client),
        patch("tai.commands.project.search_select", return_value=PROJECTS_LIST[0]),
    ):
        result = runner.invoke(main_app, ["link"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Video Research" in result.output
    manifest_text = (tmp_path / ".tai.toml").read_text()
    assert "2ef55eff03158039b95cf6e8ff60d632" in manifest_text


def test_link_user_cancels(tmp_path):
    list_client = _mock_client(PROJECTS_LIST)
    list_client.get.return_value.json.return_value = PROJECTS_LIST

    with (
        patch("tai.commands.project.find_repo_root", return_value=tmp_path),
        patch("tai.commands.project.build_client", return_value=list_client),
        patch("tai.commands.project.search_select", return_value=None),
    ):
        result = runner.invoke(main_app, ["link"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert not (tmp_path / ".tai.toml").exists()


def test_link_outside_git_repo():
    with patch("tai.commands.project.find_repo_root", return_value=None):
        result = runner.invoke(main_app, ["link"], obj=_ctx(Path("/tmp")))
    assert result.exit_code == 1


# ── tai unlink ────────────────────────────────────────────────────────────────


def test_unlink_removes_manifest(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    with patch("tai.commands.project.find_repo_root", return_value=tmp_path):
        result = runner.invoke(main_app, ["unlink"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert not (tmp_path / ".tai.toml").exists()
    assert "Unlinked" in result.output


def test_unlink_not_linked(tmp_path):
    with patch("tai.commands.project.find_repo_root", return_value=tmp_path):
        result = runner.invoke(main_app, ["unlink"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "not linked" in result.output.lower()


def test_unlink_outside_git_repo():
    with patch("tai.commands.project.find_repo_root", return_value=None):
        result = runner.invoke(main_app, ["unlink"], obj=_ctx(Path("/tmp")))
    assert result.exit_code == 1


# ── tai open ──────────────────────────────────────────────────────────────────


def test_open_github(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    with (
        patch("tai.commands.project.find_repo_root", return_value=tmp_path),
        patch("tai.commands.project.build_client", return_value=_mock_client(PROJECT_RESPONSE)),
        patch("typer.launch") as mock_launch,
    ):
        result = runner.invoke(main_app, ["open", "github"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    mock_launch.assert_called_once_with("https://github.com/TrustedAI-CO/video-research-poc")
    assert "github.com/TrustedAI-CO" in result.output


def test_open_notion(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    with (
        patch("tai.commands.project.find_repo_root", return_value=tmp_path),
        patch("tai.commands.project.build_client", return_value=_mock_client(PROJECT_RESPONSE)),
        patch("typer.launch") as mock_launch,
    ):
        result = runner.invoke(main_app, ["open", "notion"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    mock_launch.assert_called_once_with(PROJECT_RESPONSE["notion_url"])


def test_open_missing_url(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    no_drive = {**PROJECT_RESPONSE, "drive_folder": None}
    with (
        patch("tai.commands.project.find_repo_root", return_value=tmp_path),
        patch("tai.commands.project.build_client", return_value=_mock_client(no_drive)),
        patch("typer.launch"),
    ):
        result = runner.invoke(main_app, ["open", "drive"], obj=_ctx(tmp_path))

    assert result.exit_code == 1
    assert "No Drive" in result.output or "drive" in result.output.lower()


def test_open_not_linked(tmp_path):
    with patch("tai.commands.project.find_repo_root", return_value=tmp_path):
        result = runner.invoke(main_app, ["open", "github"], obj=_ctx(tmp_path))

    assert result.exit_code == 1
    assert "not linked" in result.output.lower()


def test_open_unknown_tool(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    with patch("tai.commands.project.find_repo_root", return_value=tmp_path):
        result = runner.invoke(main_app, ["open", "slack"], obj=_ctx(tmp_path))

    assert result.exit_code != 0


# ── tai project new ───────────────────────────────────────────────────────────


def test_new_creates_and_links_project(tmp_path):
    created = {
        "notion_page_id": "aabbccdd11223344aabbccdd11223344",
        "notion_url": "https://www.notion.so/aabbccdd11223344aabbccdd11223344",
        "name": "My New Project",
        "status": "Not started",
        "phase": None,
    }
    mock_client = _mock_client(created, status=201)
    mock_client.post.return_value = mock_client.get.return_value

    with (
        patch("tai.commands.project.find_repo_root", return_value=tmp_path),
        patch("tai.commands.project.build_client", return_value=mock_client),
    ):
        result = runner.invoke(
            project_app, ["new"],
            input="My New Project\nA test project\nDevelopment\n",
            obj=_ctx(tmp_path),
        )

    assert result.exit_code == 0
    assert "My New Project" in result.output
    manifest_text = (tmp_path / ".tai.toml").read_text()
    assert "aabbccdd11223344aabbccdd11223344" in manifest_text


def test_new_outside_git_repo():
    with patch("tai.commands.project.find_repo_root", return_value=None):
        result = runner.invoke(project_app, ["new"], input="Test\n\n\n", obj=_ctx(Path("/tmp")))
    assert result.exit_code == 1
