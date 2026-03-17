"""CLI tests for tai config commands."""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from tai.main import app
from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def ctx_obj():
    config = TaiConfig(
        current_profile="default",
        profiles={
            "default": ProfileConfig(api_base_url="https://api.test.internal"),
            "dev": ProfileConfig(api_base_url="http://dev.internal"),
        },
    )
    return AppContext(profile="default", config=config)


def test_config_get_known_key(runner, ctx_obj):
    result = runner.invoke(app, ["config", "get", "api_base_url"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "test.internal" in result.output


def test_config_get_unknown_key(runner, ctx_obj):
    result = runner.invoke(app, ["config", "get", "nonexistent_key"], obj=ctx_obj)
    assert result.exit_code == 1


def test_config_list(runner, ctx_obj):
    result = runner.invoke(app, ["config", "list"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "api_base_url" in result.output


def test_config_list_json(runner, ctx_obj):
    result = runner.invoke(app, ["--json", "config", "list"], obj=ctx_obj)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "config" in data
    assert "api_base_url" in data["config"]


def test_config_list_profiles(runner, ctx_obj):
    with patch("tai.commands.config.load_config", return_value=ctx_obj.config):
        result = runner.invoke(app, ["config", "list-profiles"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "default" in result.output
    assert "dev" in result.output


def test_config_set(runner, ctx_obj, tmp_path, monkeypatch):
    monkeypatch.setattr("tai.core.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("tai.core.config.CONFIG_FILE", tmp_path / "config.toml")
    with patch("tai.commands.config.load_config", return_value=ctx_obj.config), \
         patch("tai.commands.config.save_config") as mock_save:
        result = runner.invoke(app, ["config", "set", "ai_model", "claude-opus-4-6"], obj=ctx_obj)
    assert result.exit_code == 0
    mock_save.assert_called_once()


def test_config_switch_profile(runner, ctx_obj, tmp_path, monkeypatch):
    monkeypatch.setattr("tai.core.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("tai.core.config.CONFIG_FILE", tmp_path / "config.toml")
    with patch("tai.commands.config.load_config", return_value=ctx_obj.config), \
         patch("tai.commands.config.save_config"):
        result = runner.invoke(app, ["config", "switch-profile", "dev"], obj=ctx_obj)
    assert result.exit_code == 0
    assert "dev" in result.output


def test_config_switch_unknown_profile(runner, ctx_obj, tmp_path, monkeypatch):
    monkeypatch.setattr("tai.core.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("tai.core.config.CONFIG_FILE", tmp_path / "config.toml")
    with patch("tai.commands.config.load_config", return_value=ctx_obj.config):
        result = runner.invoke(app, ["config", "switch-profile", "nonexistent"], obj=ctx_obj)
    assert result.exit_code != 0
