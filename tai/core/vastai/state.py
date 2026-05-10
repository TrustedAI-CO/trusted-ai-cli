"""Per-alias state for `tai vastai` instances.

State files live under ``$XDG_CONFIG_HOME/tai/vastai/<alias>.json`` and
record everything `tai vastai down` needs to fully tear an instance back
down — instance id, ssh details, key paths, and the ssh-config alias.

Aliases are user-supplied but normalised to a safe slug; collisions are
resolved by `next_available_alias()` (suffix ``-2``, ``-3``, …).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from tai.core.errors import TaiError

_XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
STATE_DIR = _XDG_CONFIG_HOME / "tai" / "vastai"

_ALIAS_RE = re.compile(r"[^a-z0-9-]+")


class VastaiInstanceState(BaseModel):
    """Persisted record of a provisioned vast.ai instance.

    ssh_host/ssh_port default to empty so state can be saved as soon as
    `vastai create instance` returns an id — before SSH is reachable —
    making partial provisioning recoverable via `tai vastai down`.
    """

    alias: str
    instance_id: int
    ssh_host: str = ""
    ssh_port: int = 0
    ssh_user: str = "root"
    ssh_key_path: str
    ssh_config_alias: str
    repo_paths: list[str] = Field(default_factory=list)
    remote_repo_root: str = "/root"
    vastai_ssh_key_id: int | None = None
    image: str = ""
    gpu: str = ""
    disk_gb: int = 0
    region: str = "any"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def normalise_alias(alias: str) -> str:
    """Lowercase, hyphenate, strip junk. Empty or all-junk input raises."""
    cleaned = _ALIAS_RE.sub("-", alias.strip().lower()).strip("-")
    if not cleaned:
        raise TaiError(
            f"Invalid alias: {alias!r}",
            hint="Use letters, digits, and hyphens (e.g. quick-gpu).",
        )
    return cleaned


def state_dir(base: Path | None = None) -> Path:
    return (base or STATE_DIR)


def state_path(alias: str, base: Path | None = None) -> Path:
    return state_dir(base) / f"{normalise_alias(alias)}.json"


def list_aliases(base: Path | None = None) -> list[str]:
    d = state_dir(base)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def next_available_alias(requested: str, base: Path | None = None) -> str:
    """Return `requested` if free, else `requested-2`, `requested-3`, …"""
    requested = normalise_alias(requested)
    taken = set(list_aliases(base))
    if requested not in taken:
        return requested
    for i in range(2, 1000):
        candidate = f"{requested}-{i}"
        if candidate not in taken:
            return candidate
    raise TaiError("Could not allocate a unique alias", hint="Clean up old instances with `tai vastai down --all`.")


def load_state(alias: str, base: Path | None = None) -> VastaiInstanceState:
    path = state_path(alias, base)
    if not path.is_file():
        raise TaiError(
            f"No vastai instance recorded for alias {alias!r}",
            hint="Run `tai vastai list` to see known aliases.",
        )
    return VastaiInstanceState.model_validate_json(path.read_text())


def save_state(state: VastaiInstanceState, base: Path | None = None) -> Path:
    path = state_path(state.alias, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.model_dump(), indent=2, sort_keys=True))
    return path


def delete_state(alias: str, base: Path | None = None) -> bool:
    path = state_path(alias, base)
    if not path.is_file():
        return False
    path.unlink()
    return True
