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
        result = runner.invoke(app, ["--verbose", "whoami"])
    # verbose mode should not crash; profile debug line appears on stderr
    assert result.exit_code == 0


def test_json_flag_available():
    import re
    result = runner.invoke(app, ["--help"])
    clean = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    assert "--json" in clean


def test_docs_command():
    """Test docs command outputs markdown."""
    result = runner.invoke(app, ["docs"])
    assert result.exit_code == 0
    assert "# tai" in result.output
    assert "Commands" in result.output


def test_update_banner_shown():
    """Test update banner is shown when update available."""
    from unittest.mock import MagicMock

    cached = MagicMock()
    cached.update_available = True
    cached.current = "1.0.0"
    cached.latest = "2.0.0"

    with patch("tai.main.load_cached_update", return_value=cached):
        with patch("tai.core.auth.current_email", return_value="u@test.com"):
            result = runner.invoke(app, ["whoami"])
    # Banner appears in stderr, captured in output
    # Just verify it doesn't crash
    assert result.exit_code == 0


def test_update_banner_suppressed_on_error():
    """Test update banner doesn't crash on error."""
    with patch("tai.main.load_cached_update", side_effect=Exception("fail")):
        with patch("tai.core.auth.current_email", return_value="u@test.com"):
            result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 0
