"""CLI tests for tai api commands."""

import json
from unittest.mock import patch, MagicMock

import pytest
import httpx
from typer.testing import CliRunner

from tai.main import app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig
from tai.core.errors import ApiError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def ctx_obj():
    config = TaiConfig(profiles={"default": ProfileConfig(
        api_base_url="http://api.test.internal",
        oauth_client_id="test-client",
    )})
    return AppContext(profile="default", config=config)


def _mock_client(response_data: dict | str, status: int = 200):
    """Build a mock httpx client that returns a fixed response."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = response_data
    mock_resp.text = json.dumps(response_data) if isinstance(response_data, dict) else response_data

    mock_client = MagicMock()
    mock_client.__enter__ = lambda s: s
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.request.return_value = mock_resp
    mock_client.get.return_value = mock_resp
    return mock_client


def test_api_call_get(runner, ctx_obj):
    mock = _mock_client({"user": "alice"})
    with patch("tai.commands.api.build_client", return_value=mock):
        result = runner.invoke(app, ["api", "call", "/users/me"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "alice" in result.output


def test_api_call_with_params(runner, ctx_obj):
    mock = _mock_client({"items": []})
    with patch("tai.commands.api.build_client", return_value=mock):
        result = runner.invoke(app, ["api", "call", "/events", "-p", "status=active"], obj=ctx_obj)
    assert result.exit_code == 0
    mock.request.assert_called_once()
    _, kwargs = mock.request.call_args
    assert kwargs["params"]["status"] == "active"


def test_api_call_invalid_method(runner, ctx_obj):
    result = runner.invoke(app, ["api", "call", "/users", "-X", "INVALID"], obj=ctx_obj)
    assert result.exit_code == 1


def test_api_call_invalid_json_body(runner, ctx_obj):
    result = runner.invoke(app, ["api", "call", "/users", "-X", "POST", "-d", "{bad json}"], obj=ctx_obj)
    assert result.exit_code == 1


def test_api_call_invalid_param_format(runner, ctx_obj):
    result = runner.invoke(app, ["api", "call", "/users", "-p", "noequals"], obj=ctx_obj)
    assert result.exit_code == 1


def test_api_endpoints(runner, ctx_obj):
    spec = {"paths": {"/users": {"get": {"summary": "List users"}}}}
    mock = _mock_client(spec)
    with patch("tai.commands.api.build_client", return_value=mock):
        result = runner.invoke(app, ["api", "endpoints"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "/users" in result.output
