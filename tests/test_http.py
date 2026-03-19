"""Tests for http client factory and 401 auto-retry."""

from unittest.mock import patch, call

import httpx
import pytest
import respx

from tai.core.context import AppContext
from tai.core.config import TaiConfig, ProfileConfig
from tai.core.errors import ApiError, AuthError, AuthExpiredError
from tai.core.http import build_client, _BearerAuth


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
    assert client.headers["Accept"] == "application/json"


def test_build_client_raises_when_not_logged_in(app_ctx):
    with patch("tai.core.auth.get_access_token", side_effect=AuthError()):
        client = build_client(app_ctx)
        with pytest.raises(AuthError):
            client.get("http://api.test.internal/anything")


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


@respx.mock
def test_client_retries_on_401_then_succeeds(app_ctx):
    """401 → refresh token → retry → 200 (user sees nothing)."""
    route = respx.get("http://api.test.internal/data")
    route.side_effect = [
        httpx.Response(401, json={"detail": "expired"}),
        httpx.Response(200, json={"ok": True}),
    ]
    with patch("tai.core.auth.get_access_token", return_value="old-token"), \
         patch("tai.core.auth._refresh", return_value="new-token"):
        client = build_client(app_ctx)
        resp = client.get("/data")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@respx.mock
def test_client_raises_auth_expired_when_refresh_fails_on_401(app_ctx):
    """401 → refresh fails → AuthExpiredError."""
    respx.get("http://api.test.internal/data").mock(
        return_value=httpx.Response(401, json={"detail": "expired"})
    )
    with patch("tai.core.auth.get_access_token", return_value="old-token"), \
         patch("tai.core.auth._refresh", side_effect=AuthExpiredError()):
        client = build_client(app_ctx)
        with pytest.raises(AuthExpiredError):
            client.get("/data")


@respx.mock
def test_client_raises_auth_expired_on_double_401(app_ctx):
    """401 → refresh succeeds → retry 401 again → AuthExpiredError."""
    route = respx.get("http://api.test.internal/data")
    route.side_effect = [
        httpx.Response(401, json={"detail": "expired"}),
        httpx.Response(401, json={"detail": "still expired"}),
    ]
    with patch("tai.core.auth.get_access_token", return_value="old-token"), \
         patch("tai.core.auth._refresh", return_value="new-token"):
        client = build_client(app_ctx)
        with pytest.raises(AuthExpiredError):
            client.get("/data")
