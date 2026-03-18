"""Tests for error classes and handle_error."""

import pytest
import typer

from tai.core.errors import (
    TaiError, AuthError, AuthExpiredError, DomainError,
    ConfigError, SecretNotFoundError, ApiError, handle_error,
)


def test_auth_error_has_hint():
    e = AuthError()
    assert e.hint is not None
    assert "tai auth login" in e.hint


def test_auth_expired_error():
    e = AuthExpiredError()
    assert "expired" in str(e).lower()


def test_domain_error_message():
    e = DomainError("user@other.com", "trusted-ai.com")
    assert "trusted-ai.com" in str(e)


def test_secret_not_found_has_hint():
    e = SecretNotFoundError("MY_KEY")
    assert "MY_KEY" in str(e)
    assert e.hint is not None


def test_api_error():
    e = ApiError(404, "not found")
    assert "404" in str(e)
    assert e.exit_code == 3  # NOT_FOUND

def test_api_error_conflict():
    assert ApiError(409, "conflict").exit_code == 5  # CONFLICT

def test_api_error_permission():
    assert ApiError(403, "forbidden").exit_code == 4  # PERMISSION_DENIED

def test_api_error_generic():
    assert ApiError(500, "server error").exit_code == 2  # USAGE/generic


def test_handle_error_exits(capsys):
    e = TaiError("something broke", hint="try this")
    with pytest.raises(typer.Exit) as exc_info:
        handle_error(e)
    assert exc_info.value.exit_code == 1
