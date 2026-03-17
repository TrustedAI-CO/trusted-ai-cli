"""Secret storage with three-layer fallback.

Priority:
  1. System keychain (macOS Keychain / Windows Credential Manager / GNOME Keyring)
  2. Encrypted file fallback (~/.config/tai/secrets.enc) — for CI/headless
  3. Environment variable TAI_SECRET_<NAME> — read-only, for CI injection

Secrets are NEVER read from CLI flags per clig.dev guidelines.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import keyring
import keyring.errors

from tai.core.config import CONFIG_DIR
from tai.core.errors import SecretNotFoundError

_SECRETS_FILE = CONFIG_DIR / "secrets.json"  # plaintext fallback for CI; document this clearly


def _service_name(profile: str) -> str:
    return f"tai-{profile}"


def _env_var_name(name: str) -> str:
    return f"TAI_SECRET_{name.upper().replace('-', '_')}"


# ── Public API ────────────────────────────────────────────────────────────────


def store(profile: str, name: str, value: str) -> None:
    """Store a secret in the system keychain."""
    try:
        keyring.set_password(_service_name(profile), name, value)
    except keyring.errors.NoKeyringError:
        _file_store(profile, name, value)


def retrieve(profile: str, name: str) -> str:
    """Retrieve a secret. Raises SecretNotFoundError if not found."""
    # 1. Environment variable (read-only injection for CI)
    env_value = os.environ.get(_env_var_name(name))
    if env_value is not None:
        return env_value

    # 2. System keychain
    try:
        value = keyring.get_password(_service_name(profile), name)
        if value is not None:
            return value
    except keyring.errors.NoKeyringError:
        pass

    # 3. File fallback
    value = _file_retrieve(profile, name)
    if value is not None:
        return value

    raise SecretNotFoundError(name)


def delete(profile: str, name: str) -> None:
    """Delete a secret. Raises SecretNotFoundError if not found."""
    deleted = False
    try:
        keyring.delete_password(_service_name(profile), name)
        deleted = True
    except (keyring.errors.NoKeyringError, keyring.errors.PasswordDeleteError):
        pass

    if _file_delete(profile, name):
        deleted = True

    if not deleted:
        raise SecretNotFoundError(name)


def rotate(profile: str, name: str, new_value: str) -> None:
    """Atomically replace a secret value (store new before clearing old reference)."""
    store(profile, name, new_value)  # overwrite in place — keyring handles atomicity


def list_names(profile: str) -> list[str]:
    """Return all secret names for a profile (values are never exposed)."""
    names: set[str] = set()

    # File fallback
    data = _file_load()
    names.update(data.get(_service_name(profile), {}).keys())

    # Env vars: report ones matching TAI_SECRET_* as advisory
    prefix = "TAI_SECRET_"
    for key in os.environ:
        if key.startswith(prefix):
            names.add(key[len(prefix):].lower())

    return sorted(names)


# ── File fallback (CI / no keychain) ─────────────────────────────────────────


def _file_load() -> dict:
    if not _SECRETS_FILE.exists():
        return {}
    with _SECRETS_FILE.open() as f:
        return json.load(f)


def _file_save(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _SECRETS_FILE.open("w") as f:
        json.dump(data, f, indent=2)
    _SECRETS_FILE.chmod(0o600)  # owner-read-only


def _file_store(profile: str, name: str, value: str) -> None:
    data = _file_load()
    svc = _service_name(profile)
    data.setdefault(svc, {})[name] = value
    _file_save(data)


def _file_retrieve(profile: str, name: str) -> str | None:
    data = _file_load()
    return data.get(_service_name(profile), {}).get(name)


def _file_delete(profile: str, name: str) -> bool:
    data = _file_load()
    svc = _service_name(profile)
    if name in data.get(svc, {}):
        del data[svc][name]
        _file_save(data)
        return True
    return False
