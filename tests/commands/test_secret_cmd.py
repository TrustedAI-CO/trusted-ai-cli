"""CLI tests for tai secret commands."""

import json
import pytest
from unittest.mock import patch
from typer.testing import CliRunner

from tai.main import app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig
from tai.core.errors import SecretNotFoundError


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def ctx_obj():
    config = TaiConfig(profiles={"default": ProfileConfig()})
    return AppContext(profile="default", config=config)


def test_secret_list_empty(runner, ctx_obj):
    with patch("tai.core.keystore.list_names", return_value=[]):
        result = runner.invoke(app, ["secret", "list"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "No secrets" in result.output


def test_secret_list_shows_names(runner, ctx_obj):
    with patch("tai.core.keystore.list_names", return_value=["API_KEY", "DB_PASS"]):
        result = runner.invoke(app, ["secret", "list"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "DB_PASS" in result.output


def test_secret_list_json(runner, ctx_obj):
    with patch("tai.core.keystore.list_names", return_value=["API_KEY"]):
        result = runner.invoke(app, ["--json", "secret", "list"], obj=ctx_obj)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "API_KEY" in data["secrets"]


def test_secret_get(runner, ctx_obj):
    with patch("tai.core.keystore.retrieve", return_value="secret-value"):
        result = runner.invoke(app, ["secret", "get", "MY_KEY"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "secret-value" in result.output


def test_secret_get_missing(runner, ctx_obj):
    with patch("tai.core.keystore.retrieve", side_effect=SecretNotFoundError("MY_KEY")):
        result = runner.invoke(app, ["secret", "get", "MY_KEY"], obj=ctx_obj)
    assert result.exit_code != 0


def test_secret_delete_with_force(runner, ctx_obj):
    with patch("tai.core.keystore.delete") as mock_del:
        result = runner.invoke(app, ["secret", "delete", "MY_KEY", "--force"], obj=ctx_obj)
    assert result.exit_code == 0
    mock_del.assert_called_once_with("default", "MY_KEY")
