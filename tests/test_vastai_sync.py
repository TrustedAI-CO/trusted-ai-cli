"""Sync command construction and helper logic."""

from __future__ import annotations

import subprocess

import pytest

from tai.core.errors import TaiError
from tai.core.vastai import sync


def _runner(stdout: str = "", returncode: int = 0):
    def run(cmd):
        return subprocess.CompletedProcess(cmd, returncode, stdout, "")
    return run


def test_is_git_repo_true_when_git_says_so():
    assert sync.is_git_repo("/tmp", runner=_runner("true\n", 0)) is True


def test_is_git_repo_false_on_error():
    assert sync.is_git_repo("/tmp", runner=_runner("", 128)) is False


def test_uncommitted_files_combines_modified_and_untracked(monkeypatch):
    calls: list[list[str]] = []

    def runner(cmd):
        calls.append(list(cmd))
        if "diff" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "a.py\0b.py\0", "")
        if "ls-files" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "a.py\0c.py\0", "")
        return subprocess.CompletedProcess(cmd, 1, "", "")

    files = sync.uncommitted_files("/tmp", runner=runner)
    # `a.py` is in both — must dedupe and preserve order.
    assert files == ["a.py", "b.py", "c.py"]


def test_build_clone_cmd_runs_over_ssh_with_agent_forward():
    target = sync.RemoteTarget(ssh_alias="vastai-quick-gpu", remote_root="/root")
    cmd = sync.build_clone_cmd(
        target=target,
        origin_url="git@github.com:foo/bar.git",
        branch="main",
        repo_basename="bar",
    )
    assert "-A" in cmd
    assert "vastai-quick-gpu" in cmd
    assert "git clone git@github.com:foo/bar.git /root/bar --branch main" in cmd[-1]
    assert "/root/bar/.git" in cmd[-1]  # idempotent fetch branch


def test_build_rsync_cmd_returns_none_for_empty_files(tmp_path):
    target = sync.RemoteTarget(ssh_alias="vastai-quick-gpu")
    assert sync.build_rsync_cmd(
        target=target, local_root=tmp_path, files=[], repo_basename="bar"
    ) is None


def test_build_rsync_cmd_uses_files_from_stdin(tmp_path):
    target = sync.RemoteTarget(ssh_alias="vastai-quick-gpu", remote_root="/root")
    cmd = sync.build_rsync_cmd(
        target=target, local_root=tmp_path, files=["a.py", "src/b.py"], repo_basename="bar"
    )
    assert cmd is not None
    assert "--files-from=-" in cmd
    assert cmd[-1] == "vastai-quick-gpu:/root/bar/"


def test_build_rsync_ignored_cmd_includes_excludes(tmp_path):
    (tmp_path / "data").mkdir()
    target = sync.RemoteTarget(ssh_alias="vastai-quick-gpu", remote_root="/root")
    cmd = sync.build_rsync_ignored_cmd(
        target=target, local_root=tmp_path, include_path="data", repo_basename="bar"
    )
    assert "--exclude" in cmd
    assert ".git/" in cmd
    assert "node_modules/" in cmd
    assert cmd[-1].startswith("vastai-quick-gpu:/root/bar/data")


def test_build_rsync_ignored_cmd_missing_path_raises(tmp_path):
    target = sync.RemoteTarget(ssh_alias="vastai-quick-gpu")
    with pytest.raises(TaiError):
        sync.build_rsync_ignored_cmd(
            target=target, local_root=tmp_path, include_path="missing-folder", repo_basename="bar"
        )


@pytest.mark.parametrize("path,expected", [
    (".env", True),
    (".env.local", True),
    ("foo/.env.production", True),
    ("foo/data.csv", False),
    ("id_rsa", True),
    ("notes.md", False),
    ("credentials.json", True),
])
def test_is_secret_path(path, expected):
    assert sync.is_secret_path(path) is expected
