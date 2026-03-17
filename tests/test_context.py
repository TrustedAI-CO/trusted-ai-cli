"""Tests for AppContext and get_ctx."""

from unittest.mock import MagicMock

from tai.core.context import AppContext, get_ctx
from tai.core.config import TaiConfig, ProfileConfig


def test_active_profile_with_config():
    cfg = TaiConfig(
        current_profile="dev",
        profiles={"dev": ProfileConfig(api_base_url="http://dev.internal")},
    )
    ctx = AppContext(profile="dev", config=cfg)
    assert ctx.active_profile().api_base_url == "http://dev.internal"


def test_active_profile_fallback_no_config():
    ctx = AppContext()
    profile = ctx.active_profile()
    assert isinstance(profile, ProfileConfig)


def test_get_ctx_returns_app_context():
    app_ctx = AppContext(profile="staging")
    mock_typer_ctx = MagicMock()
    mock_typer_ctx.obj = app_ctx
    result = get_ctx(mock_typer_ctx)
    assert result is app_ctx


def test_get_ctx_returns_default_when_no_obj():
    mock_typer_ctx = MagicMock()
    mock_typer_ctx.obj = None
    result = get_ctx(mock_typer_ctx)
    assert isinstance(result, AppContext)


def test_get_ctx_returns_default_when_wrong_type():
    mock_typer_ctx = MagicMock()
    mock_typer_ctx.obj = {"not": "an AppContext"}
    result = get_ctx(mock_typer_ctx)
    assert isinstance(result, AppContext)
