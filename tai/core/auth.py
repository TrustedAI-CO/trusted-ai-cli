"""Google OAuth 2.0 PKCE flow with company domain restriction.

Domain is enforced at two levels:
  1. hd= parameter in authorization URL (Google pre-filters)
  2. JWT hd claim validation after token exchange (prevents bypass)

Secrets are stored in the system keychain, never in env vars or flags.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import socket
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import NamedTuple

import logging

import httpx
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from tai.core import keystore
from tai.core.errors import AuthError, AuthExpiredError, DomainError

log = logging.getLogger(__name__)

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
_CALLBACK_PORT = 8765
_SCOPES = "openid email profile"

_KEY_ACCESS = "access_token"
_KEY_REFRESH = "refresh_token"
_KEY_ID = "id_token"
_KEY_EXPIRY = "token_expiry"
_KEY_EMAIL = "email"


class TokenSet(NamedTuple):
    access_token: str
    refresh_token: str
    id_token_raw: str
    expiry: float  # unix timestamp
    email: str


# ── PKCE helpers ──────────────────────────────────────────────────────────────


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


# ── Local callback server ─────────────────────────────────────────────────────


class _CallbackCapture:
    code: str | None = None
    error: str | None = None


def _run_callback_server(capture: _CallbackCapture) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if "code" in params:
                capture.code = params["code"][0]
                body = b"<h1>Login successful! You can close this tab.</h1>"
            else:
                capture.error = params.get("error", ["unknown"])[0]
                body = b"<h1>Login failed. Check your terminal.</h1>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass  # silence HTTP logs

    server = HTTPServer(("localhost", _CALLBACK_PORT), Handler)
    server.timeout = 120
    server.handle_request()


# ── Token exchange & validation ───────────────────────────────────────────────


def _exchange_code(
    code: str,
    code_verifier: str,
    client_id: str,
    redirect_uri: str,
    client_secret: str = "",
) -> dict:
    payload: dict = {
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": code_verifier,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    if client_secret:
        payload["client_secret"] = client_secret
    resp = httpx.post(_GOOGLE_TOKEN_URL, data=payload, timeout=15)
    if not resp.is_success:
        raise AuthError(f"Token exchange failed ({resp.status_code}): {resp.text}")
    return resp.json()


def _validate_domain(id_token_raw: str, client_id: str, company_domain: str) -> str:
    """Validate JWT and enforce company domain. Returns email."""
    claims = id_token.verify_oauth2_token(
        id_token_raw,
        google_requests.Request(),
        client_id,
    )
    email: str = claims.get("email", "")
    hd: str = claims.get("hd", "")

    if hd != company_domain or not email.endswith(f"@{company_domain}"):
        raise DomainError(email or "(unknown)", company_domain)

    return email


# ── Public API ────────────────────────────────────────────────────────────────


def login(profile: str, client_id: str, company_domain: str, client_secret: str = "") -> str:
    """Run PKCE flow. Opens browser, waits for callback. Returns email."""
    verifier, challenge = _pkce_pair()
    redirect_uri = f"http://localhost:{_CALLBACK_PORT}/callback"

    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _SCOPES,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "hd": company_domain,  # Google pre-filter
        "access_type": "offline",
        "prompt": "consent",
    })
    auth_url = f"{_GOOGLE_AUTH_URL}?{params}"

    capture = _CallbackCapture()
    server_thread = Thread(target=_run_callback_server, args=(capture,), daemon=True)
    server_thread.start()

    webbrowser.open(auth_url)

    server_thread.join(timeout=130)
    if capture.error:
        raise AuthError(f"OAuth error: {capture.error}")
    if not capture.code:
        raise AuthError("Timed out waiting for Google login")

    token_data = _exchange_code(capture.code, verifier, client_id, redirect_uri, client_secret)
    email = _validate_domain(token_data["id_token"], client_id, company_domain)

    expiry = time.time() + token_data.get("expires_in", 3600)
    _store_tokens(profile, token_data["access_token"], token_data["refresh_token"],
                  token_data["id_token"], expiry, email)
    return email


def logout(profile: str) -> None:
    """Revoke tokens and clear keychain entries."""
    try:
        access = keystore.retrieve(profile, _KEY_ACCESS)
        httpx.post(_GOOGLE_REVOKE_URL, params={"token": access}, timeout=10)
    except Exception:
        pass  # best-effort revocation

    for key in (_KEY_ACCESS, _KEY_REFRESH, _KEY_ID, _KEY_EXPIRY, _KEY_EMAIL):
        try:
            keystore.delete(profile, key)
        except Exception:
            pass


def current_email(profile: str) -> str | None:
    """Return logged-in email or None."""
    try:
        return keystore.retrieve(profile, _KEY_EMAIL)
    except Exception:
        return None


def get_access_token(profile: str, client_id: str) -> str:
    """Return a valid access token, refreshing if needed."""
    try:
        expiry = float(keystore.retrieve(profile, _KEY_EXPIRY))
    except Exception:
        raise AuthError()

    if time.time() < expiry - 300:
        return keystore.retrieve(profile, _KEY_ACCESS)

    return _refresh(profile, client_id)


def _refresh(profile: str, client_id: str) -> str:
    try:
        refresh_token = keystore.retrieve(profile, _KEY_REFRESH)
    except Exception:
        raise AuthExpiredError()

    log.debug("Refreshing access token…")
    try:
        resp = httpx.post(
            _GOOGLE_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
            },
            timeout=15,
        )
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        log.debug("Token refresh failed: %s", exc)
        raise AuthError(
            "Could not refresh session — check your network connection",
        )

    if resp.status_code != 200:
        log.debug("Token refresh rejected (HTTP %s)", resp.status_code)
        raise AuthExpiredError()

    try:
        data = resp.json()
        new_token = data["access_token"]
    except (ValueError, KeyError) as exc:
        log.debug("Token refresh returned invalid response: %s", exc)
        raise AuthExpiredError()

    expiry = time.time() + data.get("expires_in", 3600)
    keystore.store(profile, _KEY_ACCESS, new_token)
    keystore.store(profile, _KEY_EXPIRY, str(expiry))
    log.debug("Token refreshed successfully")
    return new_token


def _store_tokens(
    profile: str,
    access: str,
    refresh: str,
    id_tok: str,
    expiry: float,
    email: str,
) -> None:
    keystore.store(profile, _KEY_ACCESS, access)
    keystore.store(profile, _KEY_REFRESH, refresh)
    keystore.store(profile, _KEY_ID, id_tok)
    keystore.store(profile, _KEY_EXPIRY, str(expiry))
    keystore.store(profile, _KEY_EMAIL, email)
