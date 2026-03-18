"""Tests for http client factory."""

from unittest.mock import patch

import httpx
import pytest
import respx

from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig
from tai.core.errors import ApiError, AuthError
from tai.core.http import build_client


@pytest.fixture
def app_ctx():
    cfg = TaiConfig(profiles={"default": ProfileConfig(
        api_base_url="http://api.test.internal",
        oauth_client_id="client-id",
        timeout_seconds=5,
    )})
    return AppContext(profile="default", config=cfg)


def test_build_client_sets_auth_header(app_ctx):
    with patch("tai.core.auth.get_access_token", return_value="test-token"):
        client = build_client(app_ctx)
    assert client.headers["Authorization"] == "Bearer test-token"
    assert client.headers["Accept"] == "application/json"


def test_build_client_raises_when_not_logged_in(app_ctx):
    with patch("tai.core.auth.get_access_token", side_effect=AuthError()):
        with pytest.raises(AuthError):
            build_client(app_ctx)


@respx.mock
def test_client_raises_api_error_on_4xx(app_ctx):
    respx.get("http://api.test.internal/not-found").mock(
        return_value=httpx.Response(404, json={"detail": "not found"})
    )
    with patch("tai.core.auth.get_access_token", return_value="token"):
        client = build_client(app_ctx)
        with pytest.raises(ApiError) as exc_info:
            client.get("/not-found")
    assert exc_info.value.exit_code == 3  # NOT_FOUND for 404


@respx.mock
def test_client_succeeds_on_2xx(app_ctx):
    respx.get("http://api.test.internal/ok").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    with patch("tai.core.auth.get_access_token", return_value="token"):
        client = build_client(app_ctx)
        resp = client.get("/ok")
    assert resp.json() == {"status": "ok"}
