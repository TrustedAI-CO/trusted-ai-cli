"""Tests for tai claude commands."""

from __future__ import annotations

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
