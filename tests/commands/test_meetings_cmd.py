"""Tests for tai meetings commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from tai.commands.meetings import app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig

runner = CliRunner()

MEETING_A = {
    "meeting_id": "aabbccdd11223344aabbccdd11223344",
    "short_id": "aabbccdd",
    "title": "Sprint Planning",
    "date": "2026-03-20",
    "meeting_type": ["Project meeting"],
    "lead": None,
    "notion_url": "https://notion.so/aabbccdd11223344aabbccdd11223344",
}
MEETING_B = {
    "meeting_id": "bbccddee11223344bbccddee11223344",
    "short_id": "bbccddee",
    "title": "Client Demo",
    "date": "2026-03-22",
    "meeting_type": ["Sale meeting"],
    "lead": None,
    "notion_url": "https://notion.so/bbccddee11223344bbccddee11223344",
}

MANIFEST_TOML = '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'


def _ctx(tmp_path: Path) -> AppContext:
    cfg = TaiConfig(profiles={"default": ProfileConfig(api_base_url="http://api.test")})
    return AppContext(profile="default", config=cfg)


def _mock_client(get_data=None, post_data=None) -> MagicMock:
    def _resp(data):
        r = MagicMock(spec=httpx.Response)
        r.status_code = 200
        r.json.return_value = data
        return r

    client = MagicMock()
    if get_data is not None:
        client.get.return_value = _resp(get_data)
    if post_data is not None:
        client.post.return_value = _resp(post_data)
    return client


# ── list (default callback) ───────────────────────────────────────────────────


def test_list_meetings_shows_table(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A, MEETING_B])),
    ):
        result = runner.invoke(app, [], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Sprint Planning" in result.output
    assert "Client Demo" in result.output
    assert "aabbccdd" in result.output


def test_list_meetings_empty(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[])),
    ):
        result = runner.invoke(app, [], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "No meetings" in result.output


def test_list_all_projects(tmp_path):
    with patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A, MEETING_B])):
        result = runner.invoke(app, ["-a"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Sprint Planning" in result.output
    assert "Client Demo" in result.output


def test_list_filter(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A, MEETING_B])),
    ):
        result = runner.invoke(app, ["-f", "Sprint"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Sprint Planning" in result.output
    assert "Client Demo" not in result.output


def test_list_limit(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A, MEETING_B])),
    ):
        result = runner.invoke(app, ["-n", "1"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Sprint Planning" in result.output
    assert "Client Demo" not in result.output


def test_list_meetings_no_manifest(tmp_path):
    with patch("tai.commands.meetings.find_repo_root", return_value=tmp_path):
        result = runner.invoke(app, [], obj=_ctx(tmp_path))
    assert result.exit_code == 1


def test_list_meetings_outside_git_repo():
    with patch("tai.commands.meetings.find_repo_root", return_value=None):
        result = runner.invoke(app, [], obj=_ctx(Path("/tmp")))
    assert result.exit_code == 1


# ── add ───────────────────────────────────────────────────────────────────────


def test_add_creates_meeting(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(post_data=MEETING_A)),
    ):
        result = runner.invoke(app, ["add"], input="Sprint Planning\n2026-03-20\n\n", obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Sprint Planning" in result.output
    assert "aabbccdd" in result.output


# ── open ──────────────────────────────────────────────────────────────────────


def test_open_meeting_by_id(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A, MEETING_B])),
        patch("typer.launch") as mock_launch,
    ):
        result = runner.invoke(app, ["open", "aabbccdd"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    mock_launch.assert_called_once()
    assert "aabbccdd11223344aabbccdd11223344" in mock_launch.call_args[0][0]


def test_open_meeting_fuzzy_picker(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A, MEETING_B])),
        patch("tai.commands.meetings.search_select", return_value=MEETING_A),
        patch("typer.launch") as mock_launch,
    ):
        result = runner.invoke(app, ["open"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    mock_launch.assert_called_once()


def test_open_meeting_cancelled(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A])),
        patch("tai.commands.meetings.search_select", return_value=None),
    ):
        result = runner.invoke(app, ["open"], obj=_ctx(tmp_path))

    assert result.exit_code == 0


def test_open_meeting_not_found(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[MEETING_A, MEETING_B])),
    ):
        result = runner.invoke(app, ["open", "zzzzzzzz"], obj=_ctx(tmp_path))

    assert result.exit_code == 1
    assert "No meeting found" in result.output


def test_open_meeting_ambiguous_id(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    meeting1 = {**MEETING_A, "short_id": "aabb1111"}
    meeting2 = {**MEETING_B, "short_id": "aabb2222"}
    with (
        patch("tai.commands.meetings.find_repo_root", return_value=tmp_path),
        patch("tai.commands.meetings.build_client", return_value=_mock_client(get_data=[meeting1, meeting2])),
    ):
        result = runner.invoke(app, ["open", "aabb"], obj=_ctx(tmp_path))

    assert result.exit_code == 1
    assert "Ambiguous" in result.output
