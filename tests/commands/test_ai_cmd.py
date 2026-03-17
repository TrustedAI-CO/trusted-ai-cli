"""CLI tests for tai ai commands."""

import json
from unittest.mock import patch, MagicMock

import pytest
import httpx
from typer.testing import CliRunner

from tai.main import app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def ctx_obj():
    config = TaiConfig(profiles={"default": ProfileConfig(
        ai_model="claude-haiku-4-5",
        oauth_client_id="test-client",
    )})
    return AppContext(profile="default", config=config)


def _mock_client(response_data: dict):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = response_data
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.get.return_value = mock_resp
    return mock_client


def test_ai_complete(runner, ctx_obj):
    mock = _mock_client({"text": "Hello world!"})
    with patch("tai.commands.ai.build_client", return_value=mock):
        result = runner.invoke(app, ["ai", "complete", "say hello"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "Hello world!" in result.output


def test_ai_complete_json(runner, ctx_obj):
    mock = _mock_client({"text": "Hello world!"})
    with patch("tai.commands.ai.build_client", return_value=mock):
        result = runner.invoke(app, ["--json", "ai", "complete", "say hello"], obj=ctx_obj)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["text"] == "Hello world!"


def test_ai_chat_no_stream(runner, ctx_obj):
    mock = _mock_client({"content": "Hi there!"})
    with patch("tai.commands.ai.build_client", return_value=mock):
        result = runner.invoke(app, ["ai", "chat", "hello", "--no-stream"], obj=ctx_obj)
    assert result.exit_code == 0


def test_ai_models(runner, ctx_obj):
    mock = _mock_client({"models": [{"id": "claude-sonnet-4-6", "description": "Fast model"}]})
    with patch("tai.commands.ai.build_client", return_value=mock):
        result = runner.invoke(app, ["ai", "models"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "claude-sonnet-4-6" in result.output


def test_ai_models_json(runner, ctx_obj):
    mock = _mock_client({"models": [{"id": "m1"}]})
    with patch("tai.commands.ai.build_client", return_value=mock):
        result = runner.invoke(app, ["--json", "ai", "models"], obj=ctx_obj)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "models" in data
