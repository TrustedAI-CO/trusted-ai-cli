"""Tests for tai claude commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from tai.commands.claude import (
    _build_auth_url,
    _code_challenge,
    _code_verifier,
    _parse_auth_code,
    app,
)

runner = CliRunner()


# ── fixtures for setup-hooks tests ───────────────────────────────────────────


@pytest.fixture
def fake_settings(tmp_path):
    """Provide a temp settings.json path and patch SETTINGS_PATH."""
    settings_file = tmp_path / ".claude" / "settings.json"
    settings_file.parent.mkdir(parents=True)
    with patch("tai.hooks.SETTINGS_PATH", settings_file):
        yield settings_file


# ── unit tests for helper functions ──────────────────────────────────────────


def test_code_verifier_is_url_safe_base64():
    v = _code_verifier()
    assert isinstance(v, str)
    assert len(v) > 40
    # no padding chars in URL-safe base64 without padding
    assert "=" not in v


def test_code_challenge_is_s256():
    import base64
    import hashlib

    verifier = "test_verifier_string"
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    assert _code_challenge(verifier) == expected


def test_build_auth_url_contains_required_params():
    url = _build_auth_url("my_verifier", "my_state")
    assert "claude.ai/oauth/authorize" in url
    assert "client_id=9d1c250a" in url
    assert "response_type=code" in url
    assert "state=my_state" in url
    assert "code_challenge_method=S256" in url
    assert "redirect_uri=" in url


def test_parse_auth_code_full_url():
    url = "https://platform.claude.com/oauth/code/callback?code=abc123&state=xyz"
    assert _parse_auth_code(url) == "abc123"


def test_parse_auth_code_code_hash_state():
    assert _parse_auth_code("abc123#state_value") == "abc123"


def test_parse_auth_code_bare_code():
    assert _parse_auth_code("  abc123  ") == "abc123"


def test_parse_auth_code_url_missing_code_raises():
    with pytest.raises(ValueError, match="No 'code' parameter"):
        _parse_auth_code("https://example.com/callback?state=xyz")


# ── CLI command tests ─────────────────────────────────────────────────────────


def test_login_no_claude_binary():
    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["login"])
    assert result.exit_code == 1
    assert "'claude' not found" in result.output


def test_login_happy_path(respx_mock):
    """Full happy-path: user pastes callback URL, tokens exchanged, claude runs."""
    import httpx as _httpx

    from tai.commands.claude import _TOKEN_URL

    respx_mock.post(_TOKEN_URL).mock(
        return_value=_httpx.Response(
            200,
            json={
                "access_token": "at_test",
                "refresh_token": "rt_test",
                "expires_in": 3600,
                "scope": "user:inference",
            },
        )
    )

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        callback_url = (
            "https://platform.claude.com/oauth/code/callback?code=CODE&state=STATE"
        )
        result = runner.invoke(app, ["login"], input=callback_url + "\n")

    assert result.exit_code == 0
    mock_run.assert_called_once()
    call_env = mock_run.call_args[1]["env"]
    assert call_env["CLAUDE_CODE_OAUTH_REFRESH_TOKEN"] == "rt_test"
    assert call_env["CLAUDE_CODE_OAUTH_SCOPES"] == "user:inference"


def test_login_token_exchange_failure(respx_mock):
    import httpx as _httpx

    from tai.commands.claude import _TOKEN_URL

    respx_mock.post(_TOKEN_URL).mock(
        return_value=_httpx.Response(401, text="Unauthorized")
    )

    with patch("shutil.which", return_value="/usr/bin/claude"):
        result = runner.invoke(app, ["login"], input="some_code\n")

    assert result.exit_code == 1
    assert "Token exchange failed" in result.output


def test_login_no_refresh_token_in_response(respx_mock):
    import httpx as _httpx

    from tai.commands.claude import _TOKEN_URL

    respx_mock.post(_TOKEN_URL).mock(
        return_value=_httpx.Response(200, json={"access_token": "at_only"})
    )

    with patch("shutil.which", return_value="/usr/bin/claude"):
        result = runner.invoke(app, ["login"], input="some_code\n")

    assert result.exit_code == 1
    assert "No refresh token" in result.output


def test_login_invalid_code_input():
    """Bad URL (no code param) is rejected before any HTTP call."""
    with patch("shutil.which", return_value="/usr/bin/claude"):
        result = runner.invoke(
            app,
            ["login"],
            input="https://example.com/no-code-here\n",
        )

    assert result.exit_code == 1
    assert "No 'code' parameter" in result.output


def test_login_claude_returns_nonzero(respx_mock):
    import httpx as _httpx

    from tai.commands.claude import _TOKEN_URL

    respx_mock.post(_TOKEN_URL).mock(
        return_value=_httpx.Response(
            200,
            json={
                "access_token": "at",
                "refresh_token": "rt",
                "expires_in": 3600,
                "scope": "user:inference",
            },
        )
    )

    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=5)
        result = runner.invoke(app, ["login"], input="CODE\n")

    assert result.exit_code == 5


def test_logout_no_claude_binary():
    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["logout"])
    assert result.exit_code == 1


def test_logout_delegates_to_claude():
    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(app, ["logout"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["/usr/bin/claude", "auth", "logout"])


def test_status_no_claude_binary():
    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 1


def test_status_delegates_to_claude():
    with (
        patch("shutil.which", return_value="/usr/bin/claude"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(["/usr/bin/claude", "auth", "status"])


# ── setup-hooks tests ───────────────────────────────────────────────────────


def test_setup_hooks_no_node():
    """Error when node is not installed."""
    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["setup-hooks"])
    assert result.exit_code == 1
    assert "'node' not found" in result.output


def test_setup_hooks_happy_path(fake_settings):
    """Install hooks into a fresh settings.json."""
    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks"])

    assert result.exit_code == 0
    assert "Installed" in result.output

    settings = json.loads(fake_settings.read_text())
    assert "hooks" in settings
    # Should have multiple event types
    assert len(settings["hooks"]) >= 4
    # All entries should have [tai] prefix
    for entries in settings["hooks"].values():
        for entry in entries:
            assert entry["description"].startswith("[tai]")


def test_setup_hooks_creates_settings(fake_settings):
    """Creates settings.json when it doesn't exist."""
    # Ensure the file doesn't exist
    fake_settings.unlink(missing_ok=True)

    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks"])

    assert result.exit_code == 0
    assert fake_settings.exists()
    settings = json.loads(fake_settings.read_text())
    assert "hooks" in settings


def test_setup_hooks_idempotent(fake_settings):
    """Running setup-hooks twice produces identical results."""
    with patch("shutil.which", return_value="/usr/bin/node"):
        runner.invoke(app, ["setup-hooks"])
        first = json.loads(fake_settings.read_text())

        runner.invoke(app, ["setup-hooks"])
        second = json.loads(fake_settings.read_text())

    assert first == second


def test_setup_hooks_preserves_custom_hooks(fake_settings):
    """Non-tai hooks are preserved during installation."""
    custom_settings = {
        "someOtherKey": True,
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": "echo custom"}],
                    "description": "My custom hook",
                }
            ],
        },
    }
    fake_settings.write_text(json.dumps(custom_settings))

    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks"])

    assert result.exit_code == 0
    settings = json.loads(fake_settings.read_text())

    # Custom hook is preserved
    pre_hooks = settings["hooks"]["PreToolUse"]
    custom = [h for h in pre_hooks if h["description"] == "My custom hook"]
    assert len(custom) == 1

    # tai hooks are also present
    tai = [h for h in pre_hooks if h["description"].startswith("[tai]")]
    assert len(tai) >= 1

    # Other settings keys are preserved
    assert settings["someOtherKey"] is True


def test_setup_hooks_list(fake_settings):
    """--list shows hooks without modifying settings."""
    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks", "--list"])

    assert result.exit_code == 0
    assert "PreToolUse" in result.output
    # Should not have created settings file
    assert not fake_settings.exists()


def test_setup_hooks_remove(fake_settings):
    """--remove strips tai hooks, preserves custom ones."""
    # First install
    with patch("shutil.which", return_value="/usr/bin/node"):
        runner.invoke(app, ["setup-hooks"])

    # Add a custom hook
    settings = json.loads(fake_settings.read_text())
    settings["hooks"]["PreToolUse"].append({
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "echo custom"}],
        "description": "My custom hook",
    })
    fake_settings.write_text(json.dumps(settings))

    # Remove tai hooks
    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks", "--remove"])

    assert result.exit_code == 0
    assert "Removed" in result.output

    settings = json.loads(fake_settings.read_text())
    # Only custom hook should remain
    pre_hooks = settings["hooks"]["PreToolUse"]
    assert len(pre_hooks) == 1
    assert pre_hooks[0]["description"] == "My custom hook"


def test_setup_hooks_remove_noop(fake_settings):
    """--remove when no tai hooks exist is a no-op."""
    fake_settings.write_text(json.dumps({"hooks": {}}))

    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks", "--remove"])

    assert result.exit_code == 0
    assert "No tai-managed hooks" in result.output


def test_setup_hooks_json_output(fake_settings):
    """--json flag produces valid JSON output."""
    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "installed" in data
    assert data["installed"] > 0
    assert "events" in data


def test_setup_hooks_corrupted_settings(fake_settings):
    """Clear error when settings.json has invalid JSON."""
    fake_settings.write_text("{broken json")

    with patch("shutil.which", return_value="/usr/bin/node"):
        result = runner.invoke(app, ["setup-hooks"])

    assert result.exit_code == 1
    # Rich may wrap text across lines; normalize whitespace
    normalized = " ".join(result.output.split())
    assert "invalid JSON" in normalized
