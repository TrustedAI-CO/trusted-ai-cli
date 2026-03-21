"""CLI tests for tai style commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from tai.main import app


@pytest.fixture
def runner():
    return CliRunner()


class TestStyleInstallCommand:
    """Test `tai style install` CLI."""

    def test_install_success(self, runner, tmp_path):
        dest = tmp_path / "stylelib" / "trustedai.mplstyle"

        with patch("tai.commands.style.install", return_value=dest):
            result = runner.invoke(app, ["style", "install"])

        assert result.exit_code == 0
        assert "Installed" in result.output

    def test_install_failure_exits_1(self, runner):
        from tai.core.style import StyleInstallError

        with patch("tai.commands.style.install",
                   side_effect=StyleInstallError("matplotlib is not installed")):
            result = runner.invoke(app, ["style", "install"])

        assert result.exit_code == 1

    def test_install_shows_usage_hint(self, runner, tmp_path):
        dest = tmp_path / "stylelib" / "trustedai.mplstyle"

        with patch("tai.commands.style.install", return_value=dest):
            result = runner.invoke(app, ["style", "install"])

        assert "plt.style.use" in result.output
