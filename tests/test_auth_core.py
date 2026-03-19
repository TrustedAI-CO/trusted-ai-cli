"""Tests for auth core module — token storage, retrieval, logout, current_email."""

from unittest.mock import patch

import httpx
import pytest

from tai.core import auth, keystore
from tai.core.errors import AuthError, AuthExpiredError, DomainError


def test_current_email_returns_none_when_not_logged_in():
    with patch("tai.core.keystore.retrieve", side_effect=Exception("not found")):
        assert auth.current_email("default") is None


def test_current_email_returns_stored():
    with patch("tai.core.keystore.retrieve", return_value="user@test.com"):
        assert auth.current_email("default") == "user@test.com"


def test_logout_does_not_raise_on_missing_tokens():
    with patch("tai.core.keystore.retrieve", side_effect=Exception("not found")), \
         patch("tai.core.keystore.delete", side_effect=Exception("not found")):
        # Should not raise
        auth.logout("default")


def test_get_access_token_returns_valid(monkeypatch):
    import time
    future = time.time() + 7200
    with patch("tai.core.keystore.retrieve") as mock_retrieve:
        mock_retrieve.side_effect = lambda profile, key: (
            str(future) if key == "token_expiry" else "access-token-123"
        )
        token = auth.get_access_token("default", "client-id")
    assert token == "access-token-123"


def test_get_access_token_raises_when_no_expiry():
    with patch("tai.core.keystore.retrieve", side_effect=Exception("missing")):
        with pytest.raises(AuthError):
            auth.get_access_token("default", "client-id")


def test_pkce_pair_produces_valid_values():
    verifier, challenge = auth._pkce_pair()
    assert len(verifier) > 40
    assert len(challenge) > 40
    assert verifier != challenge


def test_validate_domain_raises_for_wrong_domain():
    import time
    import base64
    import json

    # Build a fake JWT (header.payload.sig — not cryptographically valid)
    header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
    payload_data = {"email": "user@other.com", "hd": "other.com", "exp": int(time.time()) + 3600}
    payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).rstrip(b"=").decode()
    fake_token = f"{header}.{payload}.fakesig"

    from unittest.mock import patch
    with patch("google.oauth2.id_token.verify_oauth2_token",
               return_value={"email": "user@other.com", "hd": "other.com"}):
        with pytest.raises(DomainError):
            auth._validate_domain(fake_token, "client-id", "trusted-ai.com")


def test_validate_domain_succeeds_for_correct_domain():
    with patch("google.oauth2.id_token.verify_oauth2_token",
               return_value={"email": "user@trusted-ai.com", "hd": "trusted-ai.com"}):
        email = auth._validate_domain("fake.token.sig", "client-id", "trusted-ai.com")
    assert email == "user@trusted-ai.com"


# ── Refresh window & network error tests ─────────────────────────────────────


def test_get_access_token_refreshes_within_300s_window():
    """Token within 300s of expiry triggers a refresh."""
    import time
    # Expiry is 200s from now — inside the 300s window
    near_expiry = time.time() + 200
    with patch("tai.core.keystore.retrieve") as mock_retrieve, \
         patch.object(auth, "_refresh", return_value="refreshed-token") as mock_refresh:
        mock_retrieve.side_effect = lambda profile, key: (
            str(near_expiry) if key == "token_expiry" else "old-token"
        )
        token = auth.get_access_token("default", "client-id")
    assert token == "refreshed-token"
    mock_refresh.assert_called_once_with("default", "client-id")


def test_get_access_token_skips_refresh_outside_window():
    """Token with >300s remaining is returned without refresh."""
    import time
    far_expiry = time.time() + 3600
    with patch("tai.core.keystore.retrieve") as mock_retrieve, \
         patch.object(auth, "_refresh") as mock_refresh:
        mock_retrieve.side_effect = lambda profile, key: (
            str(far_expiry) if key == "token_expiry" else "valid-token"
        )
        token = auth.get_access_token("default", "client-id")
    assert token == "valid-token"
    mock_refresh.assert_not_called()


def test_refresh_raises_auth_error_on_network_timeout():
    """Network timeout during refresh raises AuthError (not a traceback)."""
    with patch("tai.core.keystore.retrieve", return_value="refresh-tok"), \
         patch("httpx.post", side_effect=httpx.TimeoutException("timed out")):
        with pytest.raises(AuthError, match="network"):
            auth._refresh("default", "client-id")


def test_refresh_raises_auth_error_on_connect_error():
    """Connection failure during refresh raises AuthError."""
    with patch("tai.core.keystore.retrieve", return_value="refresh-tok"), \
         patch("httpx.post", side_effect=httpx.ConnectError("refused")):
        with pytest.raises(AuthError, match="network"):
            auth._refresh("default", "client-id")


def test_refresh_raises_auth_expired_on_bad_status():
    """Non-200 response from Google raises AuthExpiredError."""
    mock_resp = httpx.Response(400, json={"error": "invalid_grant"})
    with patch("tai.core.keystore.retrieve", return_value="refresh-tok"), \
         patch("httpx.post", return_value=mock_resp):
        with pytest.raises(AuthExpiredError):
            auth._refresh("default", "client-id")


def test_refresh_raises_auth_expired_on_missing_access_token():
    """Response missing access_token key raises AuthExpiredError."""
    mock_resp = httpx.Response(200, json={"token_type": "Bearer"})
    with patch("tai.core.keystore.retrieve", return_value="refresh-tok"), \
         patch("httpx.post", return_value=mock_resp):
        with pytest.raises(AuthExpiredError):
            auth._refresh("default", "client-id")
