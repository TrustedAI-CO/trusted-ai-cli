"""Tests for root CLI — global flags, version, plugin loading."""

from unittest.mock import patch
from typer.testing import CliRunner

from tai.main import app


runner = CliRunner()


def test_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "tai" in result.output


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "tai" in result.output


def test_unknown_profile_exits_nonzero():
    result = runner.invoke(app, ["--profile", "nonexistent-profile", "auth", "whoami"])
    assert result.exit_code != 0


def test_verbose_flag_propagates():
    with patch("tai.core.auth.current_email", return_value="u@test.com"):
        result = runner.invoke(app, ["--verbose", "auth", "whoami"])
    # verbose mode should not crash; profile debug line appears on stderr
    assert result.exit_code == 0


def test_json_flag_available():
    result = runner.invoke(app, ["--help"])
    assert "--json" in result.output
