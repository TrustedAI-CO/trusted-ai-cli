"""CLI tests for tai auth commands."""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from tai.main import app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig
from tai.core.errors import AuthError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def ctx_obj():
    config = TaiConfig(profiles={"default": ProfileConfig(
        oauth_client_id="test-client-id",
        company_domain="test.com",
    )})
    return AppContext(profile="default", config=config)


@pytest.fixture
def ctx_no_client(ctx_obj):
    ctx_obj.config.profiles["default"] = ProfileConfig(oauth_client_id="")
    return ctx_obj


def test_login_no_client_id_exits(runner, ctx_no_client):
    result = runner.invoke(app, ["login"], obj=ctx_no_client)
    assert result.exit_code == 1


def test_login_success(runner, ctx_obj):
    with patch("tai.commands.auth.auth.login", return_value="user@test.com"):
        result = runner.invoke(app, ["login"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "user@test.com" in result.output


def test_login_auth_error(runner, ctx_obj):
    with patch("tai.core.auth.login", side_effect=AuthError("OAuth failed")):
        result = runner.invoke(app, ["login"], obj=ctx_obj)
    assert result.exit_code != 0


def test_logout_success(runner, ctx_obj):
    with patch("tai.core.auth.logout"):
        result = runner.invoke(app, ["logout"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "Logged out" in result.output


def test_whoami_logged_in(runner, ctx_obj):
    with patch("tai.core.auth.current_email", return_value="user@test.com"):
        result = runner.invoke(app, ["whoami"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "user@test.com" in result.output


def test_whoami_not_logged_in(runner, ctx_obj):
    with patch("tai.core.auth.current_email", return_value=None):
        result = runner.invoke(app, ["whoami"], obj=ctx_obj)
    assert result.exit_code == 1


def test_whoami_json(runner, ctx_obj):
    with patch("tai.core.auth.current_email", return_value="user@test.com"):
        result = runner.invoke(app, ["--json", "whoami"], obj=ctx_obj)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["email"] == "user@test.com"
