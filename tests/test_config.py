"""Tests for config loading and profile management."""

import pytest
import tomli_w
from pathlib import Path

from tai.core.config import load_config, save_config, TaiConfig, ProfileConfig
from tai.core.errors import ConfigError


@pytest.fixture(autouse=True)
def _isolated_config(tmp_path, monkeypatch):
    config_dir = tmp_path / ".config" / "tai"
    config_dir.mkdir(parents=True)
    monkeypatch.setattr("tai.core.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("tai.core.config.CONFIG_FILE", config_dir / "config.toml")
    monkeypatch.setattr("tai.core.config.PROJECT_CONFIG_FILE", tmp_path / ".tai.toml")


def test_load_returns_defaults_when_no_file():
    config = load_config()
    assert config.current_profile == "default"
    assert "default" in config.profiles


def test_profile_override():
    config = TaiConfig(
        current_profile="default",
        profiles={
            "default": ProfileConfig(),
            "dev": ProfileConfig(api_base_url="http://dev.internal"),
        },
    )
    save_config(config)
    loaded = load_config(profile_override="dev")
    assert loaded.current_profile == "dev"
    assert loaded.active().api_base_url == "http://dev.internal"


def test_unknown_profile_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config(profile_override="nonexistent")


def test_save_and_reload(tmp_path):
    config = TaiConfig(
        current_profile="staging",
        profiles={
            "staging": ProfileConfig(api_base_url="https://staging.api.internal"),
        },
    )
    save_config(config)
    reloaded = load_config()
    assert reloaded.current_profile == "staging"
    assert reloaded.active().api_base_url == "https://staging.api.internal"
