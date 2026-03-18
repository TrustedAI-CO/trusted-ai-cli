"""Tests for keystore module — uses file fallback to avoid needing a real keychain."""

import os
import pytest
from unittest.mock import patch

import keyring.errors

from tai.core import keystore
from tai.core.errors import SecretNotFoundError


@pytest.fixture(autouse=True)
def _use_file_fallback(tmp_path, monkeypatch):
    """Force file fallback by making keyring raise NoKeyringError."""
    monkeypatch.setattr(keystore, "_SECRETS_FILE", tmp_path / "secrets.json")
    with patch("keyring.set_password", side_effect=keyring.errors.NoKeyringError), \
         patch("keyring.get_password", side_effect=keyring.errors.NoKeyringError), \
         patch("keyring.delete_password", side_effect=keyring.errors.NoKeyringError):
        yield


def test_store_and_retrieve():
    keystore.store("default", "MY_KEY", "my-value")
    assert keystore.retrieve("default", "MY_KEY") == "my-value"


def test_retrieve_missing_raises():
    with pytest.raises(SecretNotFoundError):
        keystore.retrieve("default", "NONEXISTENT")


def test_delete_removes_secret():
    keystore.store("default", "DEL_KEY", "to-delete")
    keystore.delete("default", "DEL_KEY")
    with pytest.raises(SecretNotFoundError):
        keystore.retrieve("default", "DEL_KEY")


def test_rotate_replaces_value():
    keystore.store("default", "ROT_KEY", "old-value")
    keystore.rotate("default", "ROT_KEY", "new-value")
    assert keystore.retrieve("default", "ROT_KEY") == "new-value"


def test_list_names_returns_sorted(tmp_path):
    keystore.store("default", "B_KEY", "b")
    keystore.store("default", "A_KEY", "a")
    names = keystore.list_names("default")
    assert names == sorted(names)
    assert "A_KEY" in names
    assert "B_KEY" in names


def test_env_var_takes_priority(monkeypatch):
    keystore.store("default", "ENV_KEY", "from-keychain")
    monkeypatch.setenv("TAI_SECRET_ENV_KEY", "from-env")
    assert keystore.retrieve("default", "ENV_KEY") == "from-env"


def test_profile_isolation():
    keystore.store("dev", "SHARED", "dev-value")
    keystore.store("prod", "SHARED", "prod-value")
    assert keystore.retrieve("dev", "SHARED") == "dev-value"
    assert keystore.retrieve("prod", "SHARED") == "prod-value"


def test_password_set_error_falls_back_to_file(tmp_path, monkeypatch):
    """PasswordSetError (e.g. macOS keychain -25244) should fall back to file store."""
    monkeypatch.setattr(keystore, "_SECRETS_FILE", tmp_path / "secrets.json")
    with patch("keyring.set_password", side_effect=keyring.errors.PasswordSetError), \
         patch("keyring.get_password", side_effect=keyring.errors.KeyringError), \
         patch("keyring.delete_password", side_effect=keyring.errors.PasswordDeleteError):
        keystore.store("default", "FALLBACK_KEY", "fallback-value")
        assert keystore.retrieve("default", "FALLBACK_KEY") == "fallback-value"
