"""Hook management for Claude Code integration.

Provides functions to resolve bundled hook definitions and merge them
into ~/.claude/settings.json.
"""

from __future__ import annotations

import importlib.resources
import json
from pathlib import Path
from typing import Any

TAG = "[tai]"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def _hooks_package() -> Path:
    """Return the directory containing bundled hook assets."""
    return Path(str(importlib.resources.files("tai.hooks")))


def load_hook_definitions() -> dict[str, list[dict[str, Any]]]:
    """Load curated hook definitions from the bundled hooks.json."""
    hooks_json = _hooks_package() / "hooks.json"
    with hooks_json.open() as f:
        return json.load(f)


def resolve_hooks(
    definitions: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Replace relative script paths with absolute paths to bundled scripts.

    Returns a new dict (immutable pattern) with resolved commands.
    """
    scripts_dir = _hooks_package() / "scripts"
    lib_dir = _hooks_package() / "lib"
    resolved: dict[str, list[dict[str, Any]]] = {}

    for event_type, entries in definitions.items():
        resolved_entries = []
        for entry in entries:
            new_entry = {**entry}
            new_hooks = []
            for hook in entry.get("hooks", []):
                new_hook = {**hook}
                command = hook.get("command", "")
                # Replace the placeholder with absolute path
                command = command.replace(
                    "${SCRIPTS_DIR}", str(scripts_dir)
                )
                command = command.replace(
                    "${LIB_DIR}", str(lib_dir)
                )
                new_hook["command"] = command
                new_hooks.append(new_hook)
            new_entry["hooks"] = new_hooks
            resolved_entries.append(new_entry)
        resolved[event_type] = resolved_entries

    return resolved


def read_settings() -> dict[str, Any]:
    """Read ~/.claude/settings.json, returning empty dict if missing."""
    if not SETTINGS_PATH.exists():
        return {}
    text = SETTINGS_PATH.read_text(encoding="utf-8")
    return json.loads(text)


def write_settings(settings: dict[str, Any]) -> None:
    """Write settings to ~/.claude/settings.json, creating parent dirs."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings, indent=2) + "\n", encoding="utf-8"
    )


def is_tai_hook(entry: dict[str, Any]) -> bool:
    """Check whether a hook entry is managed by tai."""
    return str(entry.get("description", "")).startswith(TAG)


def merge_hooks(
    existing: dict[str, list[dict[str, Any]]],
    new_hooks: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Merge tai hooks into existing hook config.

    Removes old tai-managed hooks (by [tai] prefix), preserves custom ones,
    then appends the new tai hooks.  Returns a new dict.
    """
    merged: dict[str, list[dict[str, Any]]] = {}

    all_event_types = set(existing) | set(new_hooks)
    for event_type in all_event_types:
        # Keep non-tai hooks from existing config
        kept = [
            entry
            for entry in existing.get(event_type, [])
            if not is_tai_hook(entry)
        ]
        # Append new tai hooks
        kept.extend(new_hooks.get(event_type, []))
        merged[event_type] = kept

    return merged


def remove_tai_hooks(
    existing: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Remove all tai-managed hooks, preserving custom ones.

    Returns a new dict.  Empty event types are omitted.
    """
    cleaned: dict[str, list[dict[str, Any]]] = {}
    for event_type, entries in existing.items():
        kept = [e for e in entries if not is_tai_hook(e)]
        if kept:
            cleaned[event_type] = kept
    return cleaned
