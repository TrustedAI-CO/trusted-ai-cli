"""Tests for tai project tasks commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from tai.commands.tasks import app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig

runner = CliRunner()

TASK_A = {"task_id": "aabbccdd11223344aabbccdd11223344", "short_id": "aabbccdd", "name": "Write tests", "status": "In progress"}
TASK_B = {"task_id": "bbccddee11223344bbccddee11223344", "short_id": "bbccddee", "name": "Deploy service", "status": "Not started"}
TASK_DONE = {**TASK_A, "status": "Done"}

MANIFEST_TOML = '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'


def _ctx(tmp_path: Path) -> AppContext:
    cfg = TaiConfig(profiles={"default": ProfileConfig(api_base_url="http://api.test")})
    return AppContext(profile="default", config=cfg)


def _mock_client(get_data=None, post_data=None, patch_data=None) -> MagicMock:
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
    if patch_data is not None:
        client.patch.return_value = _resp(patch_data)
    return client


# ── list (default callback) ───────────────────────────────────────────────────


def test_list_renders_tasks(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=_mock_client(get_data=[TASK_A, TASK_B])),
    ):
        result = runner.invoke(app, [], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Write tests" in result.output
    assert "Deploy service" in result.output
    assert "aabbccdd" in result.output


def test_list_empty(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=_mock_client(get_data=[])),
    ):
        result = runner.invoke(app, [], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "No tasks" in result.output


def test_list_all_projects(tmp_path):
    with patch("tai.commands.tasks.build_client", return_value=_mock_client(get_data=[TASK_A, TASK_B])):
        result = runner.invoke(app, ["-a"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Write tests" in result.output
    assert "Deploy service" in result.output


def test_list_filter(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=_mock_client(get_data=[TASK_A, TASK_B])),
    ):
        result = runner.invoke(app, ["-f", "Write"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Write tests" in result.output
    assert "Deploy service" not in result.output


def test_list_limit(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=_mock_client(get_data=[TASK_A, TASK_B])),
    ):
        result = runner.invoke(app, ["-n", "1"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Write tests" in result.output
    assert "Deploy service" not in result.output


def test_list_no_manifest(tmp_path):
    with patch("tai.commands.tasks.find_repo_root", return_value=tmp_path):
        result = runner.invoke(app, [], obj=_ctx(tmp_path))
    assert result.exit_code == 1


def test_list_outside_git_repo():
    with patch("tai.commands.tasks.find_repo_root", return_value=None):
        result = runner.invoke(app, [], obj=_ctx(Path("/tmp")))
    assert result.exit_code == 1


# ── add ───────────────────────────────────────────────────────────────────────


def test_add_creates_task(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=_mock_client(post_data=TASK_A)),
    ):
        result = runner.invoke(app, ["add"], input="Write tests\n", obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Write tests" in result.output
    assert "aabbccdd" in result.output


# ── done ──────────────────────────────────────────────────────────────────────


def test_done_marks_task_complete_by_id(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    mock_client = _mock_client(get_data=[TASK_A, TASK_B], patch_data=TASK_DONE)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=mock_client),
    ):
        result = runner.invoke(app, ["done", "aabbccdd"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Done" in result.output
    assert "Write tests" in result.output


def test_done_interactive_picker(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    mock_client = _mock_client(get_data=[TASK_A, TASK_B], patch_data=TASK_DONE)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=mock_client),
        patch("tai.commands.tasks.search_select", return_value=TASK_A),
    ):
        result = runner.invoke(app, ["done"], obj=_ctx(tmp_path))

    assert result.exit_code == 0
    assert "Done" in result.output
    assert "Write tests" in result.output


def test_done_interactive_cancelled(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    mock_client = _mock_client(get_data=[TASK_A, TASK_B])
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=mock_client),
        patch("tai.commands.tasks.search_select", return_value=None),
    ):
        result = runner.invoke(app, ["done"], obj=_ctx(tmp_path))

    assert result.exit_code == 0


def test_done_not_found(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=_mock_client(get_data=[TASK_A, TASK_B])),
    ):
        result = runner.invoke(app, ["done", "zzzzzzzz"], obj=_ctx(tmp_path))

    assert result.exit_code == 1
    assert "No task found" in result.output


def test_done_ambiguous_id(tmp_path):
    (tmp_path / ".tai.toml").write_text(MANIFEST_TOML)
    # two tasks sharing the same prefix
    task1 = {**TASK_A, "task_id": "aabb1111" + "0" * 16, "short_id": "aabb1111"}
    task2 = {**TASK_B, "task_id": "aabb2222" + "0" * 16, "short_id": "aabb2222"}
    with (
        patch("tai.commands.tasks.find_repo_root", return_value=tmp_path),
        patch("tai.commands.tasks.build_client", return_value=_mock_client(get_data=[task1, task2])),
    ):
        result = runner.invoke(app, ["done", "aabb"], obj=_ctx(tmp_path))

    assert result.exit_code == 1
    assert "Ambiguous" in result.output
