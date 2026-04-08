"""Integration tests for tai browser commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from tai.core.browser_setup import BrowserStatus
from tai.core.context import AppContext
from tai.core.errors import BrowserError, BunNotFoundError
from tai.main import app

runner = CliRunner()


def _ctx(**overrides) -> AppContext:
    defaults = {"profile": "default", "verbose": False, "json_output": False, "config": None}
    defaults.update(overrides)
    return AppContext(**defaults)


# ── install ──────────────────────────────────────────────────────────────────


def test_browser_install_success():
    binary = Path("/fake/browse")
    with patch("tai.core.browser_setup.install_browse", return_value=binary):
        result = runner.invoke(app, ["browser", "install"], obj=_ctx())
        assert result.exit_code == 0
        assert "installed successfully" in result.output


def test_browser_install_no_bun():
    with patch(
        "tai.core.browser_setup.install_browse",
        side_effect=BunNotFoundError(),
    ):
        result = runner.invoke(app, ["browser", "install"], obj=_ctx())
        assert result.exit_code != 0


def test_browser_install_failure():
    with patch(
        "tai.core.browser_setup.install_browse",
        side_effect=BrowserError("clone failed", hint="check network"),
    ):
        result = runner.invoke(app, ["browser", "install"], obj=_ctx())
        assert result.exit_code != 0


def test_browser_install_json():
    binary = Path("/fake/browse")
    with patch("tai.core.browser_setup.install_browse", return_value=binary):
        result = runner.invoke(app, ["browser", "install"], obj=_ctx(json_output=True))
        assert result.exit_code == 0
        assert '"status": "ok"' in result.output


# ── status ───────────────────────────────────────────────────────────────────


def test_browser_status_installed():
    status = BrowserStatus(installed=True, binary_path=Path("/fake/browse"), version="0.15")
    with (
        patch("tai.commands.browser.get_browser_status", return_value=status),
        patch("tai.commands.browser.check_bun", return_value=True),
    ):
        result = runner.invoke(app, ["browser", "status"], obj=_ctx())
        assert result.exit_code == 0
        assert "/fake/browse" in result.output


def test_browser_status_not_installed():
    status = BrowserStatus(installed=False, binary_path=None, version=None)
    with (
        patch("tai.commands.browser.get_browser_status", return_value=status),
        patch("tai.commands.browser.check_bun", return_value=False),
    ):
        result = runner.invoke(app, ["browser", "status"], obj=_ctx())
        assert result.exit_code == 0
        assert "not installed" in result.output


def test_browser_status_json():
    status = BrowserStatus(installed=True, binary_path=Path("/fake/browse"), version="0.15")
    with patch("tai.commands.browser.get_browser_status", return_value=status):
        result = runner.invoke(app, ["browser", "status"], obj=_ctx(json_output=True))
        assert result.exit_code == 0
        assert '"installed": true' in result.output
