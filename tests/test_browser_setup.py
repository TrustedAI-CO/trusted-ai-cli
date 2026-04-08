"""Unit tests for tai.core.browser_setup."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tai.core.browser_setup import (
    BROWSE_BINARY,
    BROWSE_DIR,
    SKILL_LINK,
    BrowserStatus,
    check_browse_binary,
    check_bun,
    get_browser_status,
    install_browse,
)
from tai.core.errors import BrowserError, BunNotFoundError


# ── check_bun ────────────────────────────────────────────────────────────────


def test_check_bun_found():
    with patch("tai.core.browser_setup.shutil.which", return_value="/usr/local/bin/bun"):
        assert check_bun() is True


def test_check_bun_not_found():
    with patch("tai.core.browser_setup.shutil.which", return_value=None):
        assert check_bun() is False


# ── check_browse_binary ──────────────────────────────────────────────────────


def test_check_browse_binary_exists(tmp_path: Path):
    binary = tmp_path / "browse"
    binary.write_text("#!/bin/sh\necho hi")
    binary.chmod(0o755)

    with patch("tai.core.browser_setup.BROWSE_BINARY", binary):
        assert check_browse_binary() == binary


def test_check_browse_binary_not_exists(tmp_path: Path):
    with patch("tai.core.browser_setup.BROWSE_BINARY", tmp_path / "nope"):
        assert check_browse_binary() is None


def test_check_browse_binary_not_executable(tmp_path: Path):
    binary = tmp_path / "browse"
    binary.write_text("data")
    binary.chmod(0o644)

    with patch("tai.core.browser_setup.BROWSE_BINARY", binary):
        assert check_browse_binary() is None


# ── install_browse ───────────────────────────────────────────────────────────


def test_install_browse_no_bun():
    with patch("tai.core.browser_setup.check_bun", return_value=False):
        with pytest.raises(BunNotFoundError):
            install_browse()


def test_install_browse_success(tmp_path: Path):
    browse_dir = tmp_path / "browse_out"
    browse_binary = browse_dir / "browse"
    skill_link = tmp_path / "skill" / "browse"

    # Simulate the gstack build producing a binary in the tempdir
    def fake_run(cmd, *, cwd=None, error_message):
        if cmd[0] == "git" and "clone" in cmd:
            clone_target = Path(cmd[-1])
            dist = clone_target / "browse" / "dist"
            dist.mkdir(parents=True)
            (dist / "browse").write_text("#!/bin/sh\necho ok")
            (dist / "browse").chmod(0o755)
        return subprocess.CompletedProcess(cmd, 0)

    with (
        patch("tai.core.browser_setup.check_bun", return_value=True),
        patch("tai.core.browser_setup._run", side_effect=fake_run),
        patch("tai.core.browser_setup.BROWSE_DIR", browse_dir),
        patch("tai.core.browser_setup.BROWSE_BINARY", browse_binary),
        patch("tai.core.browser_setup.SKILL_LINK", skill_link),
    ):
        result = install_browse(ref="main")
        assert result == browse_binary
        assert browse_binary.exists()


def test_install_browse_clone_fails():
    with (
        patch("tai.core.browser_setup.check_bun", return_value=True),
        patch(
            "tai.core.browser_setup._run",
            side_effect=BrowserError("Failed to clone gstack repository"),
        ),
    ):
        with pytest.raises(BrowserError, match="clone"):
            install_browse()


def test_install_browse_build_fails(tmp_path: Path):
    call_count = 0

    def fake_run(cmd, *, cwd=None, error_message):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # git clone succeeds
            clone_target = Path(cmd[-1])
            clone_target.mkdir(parents=True, exist_ok=True)
            return subprocess.CompletedProcess(cmd, 0)
        if call_count == 2:  # bun install succeeds
            return subprocess.CompletedProcess(cmd, 0)
        # bun build fails
        raise BrowserError("bun run build failed in gstack")

    with (
        patch("tai.core.browser_setup.check_bun", return_value=True),
        patch("tai.core.browser_setup._run", side_effect=fake_run),
    ):
        with pytest.raises(BrowserError, match="build failed"):
            install_browse()


def test_install_browse_binary_missing_after_build():
    """Build succeeds but binary doesn't appear."""
    def fake_run(cmd, *, cwd=None, error_message):
        if cmd[0] == "git" and "clone" in cmd:
            clone_target = Path(cmd[-1])
            clone_target.mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(cmd, 0)

    with (
        patch("tai.core.browser_setup.check_bun", return_value=True),
        patch("tai.core.browser_setup._run", side_effect=fake_run),
    ):
        with pytest.raises(BrowserError, match="not found after build"):
            install_browse()


# ── _ensure_skill_link ───────────────────────────────────────────────────────


def test_ensure_skill_link(tmp_path: Path):
    from tai.core.browser_setup import _ensure_skill_link

    binary = tmp_path / "browse"
    binary.write_text("binary")
    skill_link = tmp_path / "skill" / "browse"

    with (
        patch("tai.core.browser_setup.BROWSE_BINARY", binary),
        patch("tai.core.browser_setup.SKILL_LINK", skill_link),
    ):
        _ensure_skill_link()
        link = skill_link / "dist" / "browse"
        assert link.is_symlink()
        assert link.resolve() == binary.resolve()


def test_ensure_skill_link_replaces_existing(tmp_path: Path):
    from tai.core.browser_setup import _ensure_skill_link

    binary = tmp_path / "browse"
    binary.write_text("new-binary")
    skill_link = tmp_path / "skill" / "browse"
    dist = skill_link / "dist"
    dist.mkdir(parents=True)
    old_link = dist / "browse"
    old_link.write_text("old")

    with (
        patch("tai.core.browser_setup.BROWSE_BINARY", binary),
        patch("tai.core.browser_setup.SKILL_LINK", skill_link),
    ):
        _ensure_skill_link()
        link = dist / "browse"
        assert link.is_symlink()
        assert link.resolve() == binary.resolve()


# ── get_browser_status ───────────────────────────────────────────────────────


def test_get_browser_status_installed(tmp_path: Path):
    binary = tmp_path / "browse"
    binary.write_text("#!/bin/sh")
    binary.chmod(0o755)

    with (
        patch("tai.core.browser_setup.BROWSE_BINARY", binary),
        patch("tai.core.browser_setup._read_version", return_value="0.15.15"),
    ):
        status = get_browser_status()
        assert status.installed is True
        assert status.binary_path == binary
        assert status.version == "0.15.15"


def test_get_browser_status_not_installed(tmp_path: Path):
    with patch("tai.core.browser_setup.BROWSE_BINARY", tmp_path / "nope"):
        status = get_browser_status()
        assert status.installed is False
        assert status.binary_path is None
        assert status.version is None


# ── _read_version ────────────────────────────────────────────────────────────


def test_read_version_success(tmp_path: Path):
    from tai.core.browser_setup import _read_version

    with patch("tai.core.browser_setup.BROWSE_BINARY", tmp_path / "browse"):
        with patch("tai.core.browser_setup.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="0.15.15\n")
            assert _read_version() == "0.15.15"


def test_read_version_fails(tmp_path: Path):
    from tai.core.browser_setup import _read_version

    with patch("tai.core.browser_setup.BROWSE_BINARY", tmp_path / "browse"):
        with patch("tai.core.browser_setup.subprocess.run", side_effect=OSError("boom")):
            assert _read_version() is None
