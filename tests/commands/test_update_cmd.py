"""CLI integration tests for tai update command."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig
from tai.core.updater import (
    ReleaseAsset,
    ReleaseInfo,
    UpdateCheck,
    UpdateError,
)
from tai.main import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def ctx_obj():
    config = TaiConfig(
        current_profile="default",
        profiles={"default": ProfileConfig()},
    )
    return AppContext(profile="default", config=config)


ASSET = ReleaseAsset(name="trusted_ai_cli-0.3.0-py3-none-any.whl", url="https://x", size=100)
RELEASE = ReleaseInfo(tag="v0.3.0", version="0.3.0", asset=ASSET)
UPDATE_AVAILABLE = UpdateCheck(current="0.2.0", latest="0.3.0", update_available=True, release=RELEASE)
UP_TO_DATE = UpdateCheck(current="0.3.0", latest="0.3.0", update_available=False)


def test_update_check_available(runner, ctx_obj):
    with patch("tai.commands.update.check_update", return_value=UPDATE_AVAILABLE), \
         patch("tai.commands.update.save_update_cache"):
        result = runner.invoke(app, ["update", "--check"], obj=ctx_obj)

    assert result.exit_code == 0
    assert "0.2.0" in result.output
    assert "0.3.0" in result.output


def test_update_check_up_to_date(runner, ctx_obj):
    with patch("tai.commands.update.check_update", return_value=UP_TO_DATE), \
         patch("tai.commands.update.save_update_cache"):
        result = runner.invoke(app, ["update", "--check"], obj=ctx_obj)

    assert result.exit_code == 0
    assert "up to date" in result.output


def test_update_check_json(runner, ctx_obj):
    ctx_obj.json_output = True

    with patch("tai.commands.update.check_update", return_value=UPDATE_AVAILABLE), \
         patch("tai.commands.update.save_update_cache"):
        result = runner.invoke(app, ["update", "--check"], obj=ctx_obj)

    assert result.exit_code == 0
    assert '"update_available": true' in result.output


def test_update_already_current(runner, ctx_obj):
    with patch("tai.commands.update.check_update", return_value=UP_TO_DATE), \
         patch("tai.commands.update.save_update_cache"):
        result = runner.invoke(app, ["update"], obj=ctx_obj)

    assert result.exit_code == 0
    assert "up to date" in result.output


def test_update_full_flow(runner, ctx_obj, tmp_path):
    wheel_path = tmp_path / "fake.whl"
    wheel_path.write_bytes(b"wheel")

    with patch("tai.commands.update.check_update", return_value=UPDATE_AVAILABLE), \
         patch("tai.commands.update.save_update_cache"), \
         patch("tai.commands.update.detect_installer") as mock_detect, \
         patch("tai.commands.update.download_wheel", return_value=wheel_path), \
         patch("tai.commands.update.install_wheel"), \
         patch("tai.commands.update.clear_update_cache"), \
         patch("tai.commands.update.run_post_update", return_value=(True, True, True)):
        from tai.core.updater import Installer
        mock_detect.return_value = Installer.PIP
        result = runner.invoke(app, ["update"], obj=ctx_obj)

    assert result.exit_code == 0
    assert "0.3.0" in result.output
    assert "Skills refreshed" in result.output
    assert "Hooks refreshed" in result.output
    assert "Templates refreshed" in result.output


def test_update_download_fails(runner, ctx_obj):
    with patch("tai.commands.update.check_update", return_value=UPDATE_AVAILABLE), \
         patch("tai.commands.update.save_update_cache"), \
         patch("tai.commands.update.detect_installer"), \
         patch("tai.commands.update.download_wheel", side_effect=UpdateError("Network error", hint="Retry")):
        result = runner.invoke(app, ["update"], obj=ctx_obj)

    assert result.exit_code == 1
    assert "Network error" in result.output


def test_update_install_fails(runner, ctx_obj, tmp_path):
    wheel_path = tmp_path / "fake.whl"
    wheel_path.write_bytes(b"wheel")

    with patch("tai.commands.update.check_update", return_value=UPDATE_AVAILABLE), \
         patch("tai.commands.update.save_update_cache"), \
         patch("tai.commands.update.detect_installer"), \
         patch("tai.commands.update.download_wheel", return_value=wheel_path), \
         patch("tai.commands.update.install_wheel", side_effect=UpdateError("Permission denied")):
        result = runner.invoke(app, ["update"], obj=ctx_obj)

    assert result.exit_code == 1
    assert "Permission denied" in result.output


def test_update_post_setup_partial_failure(runner, ctx_obj, tmp_path):
    wheel_path = tmp_path / "fake.whl"
    wheel_path.write_bytes(b"wheel")

    with patch("tai.commands.update.check_update", return_value=UPDATE_AVAILABLE), \
         patch("tai.commands.update.save_update_cache"), \
         patch("tai.commands.update.detect_installer") as mock_detect, \
         patch("tai.commands.update.download_wheel", return_value=wheel_path), \
         patch("tai.commands.update.install_wheel"), \
         patch("tai.commands.update.clear_update_cache"), \
         patch("tai.commands.update.run_post_update", return_value=(True, False, True)):
        from tai.core.updater import Installer
        mock_detect.return_value = Installer.PIP
        result = runner.invoke(app, ["update"], obj=ctx_obj)

    assert result.exit_code == 0
    assert "Skills refreshed" in result.output
    assert "Templates refreshed" in result.output


def test_update_check_error(runner, ctx_obj):
    with patch("tai.commands.update.check_update", side_effect=UpdateError("No releases found")):
        result = runner.invoke(app, ["update"], obj=ctx_obj)

    assert result.exit_code == 1
    assert "No releases found" in result.output
