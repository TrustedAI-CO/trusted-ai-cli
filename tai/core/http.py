"""Authenticated httpx client factory.

Every command calls build_client(ctx) — never constructs requests directly.
Auto-refreshes tokens on 401. Adds Accept: application/json header.
"""

from __future__ import annotations

import httpx

from tai.core.context import AppContext
from tai.core import auth
from tai.core.errors import AuthError, ApiError


def build_client(ctx: AppContext) -> httpx.Client:
    """Return a pre-configured httpx.Client with bearer token and base URL."""
    profile_cfg = ctx.active_profile()

    try:
        token = auth.get_access_token(ctx.profile, profile_cfg.oauth_client_id)
    except AuthError:
        raise

    return httpx.Client(
        base_url=profile_cfg.api_base_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=profile_cfg.timeout_seconds,
        event_hooks={"response": [_raise_on_error]},
    )


def _raise_on_error(response: httpx.Response) -> None:
    if response.status_code >= 400:
        response.read()  # ensure body is available before accessing it
        try:
            body = response.json().get("detail", response.text)
        except Exception:
            body = response.text
        raise ApiError(response.status_code, body)
