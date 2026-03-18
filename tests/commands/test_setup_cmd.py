"""CLI tests for tai setup command."""

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
            "default": ProfileConfig(
                api_base_url="https://api.test.internal",
                ai_model="claude-sonnet-4-6",
                timeout_seconds=30,
            ),
        },
    )
    return AppContext(profile="default", config=config)


def test_setup_skip_all_with_enter(runner, ctx_obj):
    """Pressing Enter for every prompt keeps current values — no changes saved."""
    num_fields = len(ProfileConfig.model_fields)
    user_input = "\n" * num_fields

    with patch("tai.commands.setup.is_interactive", return_value=True), \
         patch("tai.commands.setup.load_config", return_value=ctx_obj.config), \
         patch("tai.commands.setup.save_config") as mock_save:
        result = runner.invoke(app, ["setup"], input=user_input, obj=ctx_obj)

    assert result.exit_code == 0
    assert "No changes made" in result.output
    mock_save.assert_not_called()


def test_setup_updates_single_field(runner, ctx_obj):
    """Typing a new value for one field saves only that change."""
    fields = list(ProfileConfig.model_fields.keys())
    inputs = []
    for field_name in fields:
        if field_name == "ai_model":
            inputs.append("claude-opus-4-6")
        else:
            inputs.append("")
    user_input = "\n".join(inputs) + "\n"

    with patch("tai.commands.setup.is_interactive", return_value=True), \
         patch("tai.commands.setup.load_config", return_value=ctx_obj.config), \
         patch("tai.commands.setup.save_config") as mock_save:
        result = runner.invoke(app, ["setup"], input=user_input, obj=ctx_obj)

    assert result.exit_code == 0
    assert "1 change(s)" in result.output
    mock_save.assert_called_once()
    saved_config = mock_save.call_args[0][0]
    assert saved_config.profiles["default"].ai_model == "claude-opus-4-6"


def test_setup_updates_multiple_fields(runner, ctx_obj):
    """Typing new values for multiple fields saves all changes."""
    fields = list(ProfileConfig.model_fields.keys())
    inputs = []
    for field_name in fields:
        if field_name == "api_base_url":
            inputs.append("https://new-api.internal")
        elif field_name == "timeout_seconds":
            inputs.append("60")
        else:
            inputs.append("")
    user_input = "\n".join(inputs) + "\n"

    with patch("tai.commands.setup.is_interactive", return_value=True), \
         patch("tai.commands.setup.load_config", return_value=ctx_obj.config), \
         patch("tai.commands.setup.save_config") as mock_save:
        result = runner.invoke(app, ["setup"], input=user_input, obj=ctx_obj)

    assert result.exit_code == 0
    assert "2 change(s)" in result.output
    saved_config = mock_save.call_args[0][0]
    assert saved_config.profiles["default"].api_base_url == "https://new-api.internal"
    assert saved_config.profiles["default"].timeout_seconds == 60


def test_setup_non_interactive_exits(runner, ctx_obj):
    """Non-interactive terminal prints error and exits 1."""
    with patch("tai.commands.setup.is_interactive", return_value=False):
        result = runner.invoke(app, ["setup"], obj=ctx_obj)

    assert result.exit_code == 1
    assert "interactive terminal" in result.output


def test_setup_masks_sensitive_fields(runner, ctx_obj):
    """Sensitive fields like oauth_client_secret show masked values."""
    ctx_obj.config.profiles["default"] = ProfileConfig(oauth_client_secret="super-secret-value")
    num_fields = len(ProfileConfig.model_fields)
    user_input = "\n" * num_fields

    with patch("tai.commands.setup.is_interactive", return_value=True), \
         patch("tai.commands.setup.load_config", return_value=ctx_obj.config), \
         patch("tai.commands.setup.save_config"):
        result = runner.invoke(app, ["setup"], input=user_input, obj=ctx_obj)

    assert result.exit_code == 0
    assert "super-secret-value" not in result.output
    assert "****" in result.output


def test_setup_coerces_int_field(runner, ctx_obj):
    """Integer fields like timeout_seconds are coerced from string input."""
    fields = list(ProfileConfig.model_fields.keys())
    inputs = []
    for field_name in fields:
        if field_name == "timeout_seconds":
            inputs.append("120")
        else:
            inputs.append("")
    user_input = "\n".join(inputs) + "\n"

    with patch("tai.commands.setup.is_interactive", return_value=True), \
         patch("tai.commands.setup.load_config", return_value=ctx_obj.config), \
         patch("tai.commands.setup.save_config") as mock_save:
        result = runner.invoke(app, ["setup"], input=user_input, obj=ctx_obj)

    assert result.exit_code == 0
    saved_config = mock_save.call_args[0][0]
    assert saved_config.profiles["default"].timeout_seconds == 120
    assert isinstance(saved_config.profiles["default"].timeout_seconds, int)
