"""Authenticated httpx client factory.

Every command calls build_client(ctx) — never constructs requests directly.
Auto-refreshes tokens on 401 via _BearerAuth flow. Adds Accept: application/json header.
"""

from __future__ import annotations

import logging
from typing import Generator

import httpx

from tai.core.context import AppContext
from tai.core import auth
from tai.core.errors import AuthError, AuthExpiredError, ApiError

log = logging.getLogger(__name__)


class _BearerAuth(httpx.Auth):
    """httpx Auth flow that refreshes the token and retries once on 401."""

    def __init__(self, profile: str, client_id: str):
        self._profile = profile
        self._client_id = client_id

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        token = auth.get_access_token(self._profile, self._client_id)
        request.headers["Authorization"] = f"Bearer {token}"

        response = yield request

        if response.status_code == 401:
            log.debug("Received 401 — refreshing token and retrying")
            try:
                token = auth._refresh(self._profile, self._client_id)
            except (AuthError, AuthExpiredError):
                raise AuthExpiredError()
            request.headers["Authorization"] = f"Bearer {token}"
            retry_response = yield request
            if retry_response.status_code == 401:
                raise AuthExpiredError()


def build_client(ctx: AppContext) -> httpx.Client:
    """Return a pre-configured httpx.Client with bearer token and base URL."""
    profile_cfg = ctx.active_profile()

    return httpx.Client(
        base_url=profile_cfg.api_base_url,
        auth=_BearerAuth(ctx.profile, profile_cfg.oauth_client_id),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=profile_cfg.timeout_seconds,
        event_hooks={"response": [_raise_on_error]},
    )


def _raise_on_error(response: httpx.Response) -> None:
    # 401 is handled by _BearerAuth.auth_flow — skip it here
    if response.status_code == 401:
        return
    if response.status_code >= 400:
        response.read()
        try:
            body = response.json().get("detail", response.text)
        except Exception:
            body = response.text
        raise ApiError(response.status_code, body)
