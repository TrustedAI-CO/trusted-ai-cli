"""Additional tests for tai secret — rotate, exec, export flag."""

import os
from unittest.mock import patch, MagicMock

import pytest
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


def test_secret_get_export_flag(runner, ctx_obj):
    with patch("tai.core.keystore.retrieve", return_value="my-value"):
        result = runner.invoke(app, ["secret", "get", "MY_KEY", "--export"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "export MY_KEY=my-value" in result.output


def test_secret_rotate(runner, ctx_obj):
    with patch("tai.core.keystore.rotate") as mock_rotate:
        result = runner.invoke(
            app, ["secret", "rotate", "MY_KEY"], obj=ctx_obj,
            input="new-value\nnew-value\n",
        )
    assert result.exit_code == 0
    mock_rotate.assert_called_once_with("default", "MY_KEY", "new-value")


def test_secret_set(runner, ctx_obj):
    with patch("tai.core.keystore.store") as mock_store:
        result = runner.invoke(
            app, ["secret", "set", "API_KEY"], obj=ctx_obj,
            input="my-secret\nmy-secret\n",
        )
    assert result.exit_code == 0
    mock_store.assert_called_once_with("default", "API_KEY", "my-secret")


def test_secret_exec_injects_env(runner, ctx_obj):
    with patch("tai.core.keystore.list_names", return_value=["DB_URL"]), \
         patch("tai.core.keystore.retrieve", return_value="postgres://localhost/db"), \
         patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
        result = runner.invoke(
            app, ["secret", "exec", "--", "echo", "hi"], obj=ctx_obj
        )
    assert result.exit_code == 0
    call_env = mock_run.call_args[1]["env"]
    assert call_env["DB_URL"] == "postgres://localhost/db"


def test_secret_exec_no_command(runner, ctx_obj):
    with patch("tai.core.keystore.list_names", return_value=[]):
        result = runner.invoke(app, ["secret", "exec"], obj=ctx_obj)
    # Typer returns 2 for missing required argument (no command specified)
    assert result.exit_code != 0
