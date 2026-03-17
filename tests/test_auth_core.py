"""Tests for auth core module — token storage, retrieval, logout, current_email."""

from unittest.mock import patch

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
