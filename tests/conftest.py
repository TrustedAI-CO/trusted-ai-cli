"""Shared fixtures for all tests."""

import pytest
from typer.testing import CliRunner

from tai.main import app
from tai.core.context import AppContext
from tai.core.config import ProfileConfig, TaiConfig


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def default_profile():
    return ProfileConfig(
        api_base_url="http://test.internal",
        ai_model="claude-haiku-4-5",
        company_domain="test.com",
        oauth_client_id="test-client-id",
    )


@pytest.fixture
def app_ctx(default_profile):
    config = TaiConfig(
        current_profile="default",
        profiles={"default": default_profile},
    )
    return AppContext(profile="default", config=config)
