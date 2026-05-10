"""Idempotent ~/.ssh/config block writer keyed by alias.

Each instance owns a delimited block:

    # >>> tai vastai: <alias> >>>
    Host vastai-<alias>
        HostName ...
        ...
    # <<< tai vastai: <alias> <<<

`upsert_block` replaces an existing block with the same alias rather than
appending duplicates. `remove_block` strips it without touching anything
else in the file.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

DEFAULT_SSH_CONFIG = Path.home() / ".ssh" / "config"

_BEGIN = "# >>> tai vastai: {alias} >>>"
_END = "# <<< tai vastai: {alias} <<<"


def block_markers(alias: str) -> tuple[str, str]:
    return _BEGIN.format(alias=alias), _END.format(alias=alias)


def host_alias(alias: str) -> str:
    return f"vastai-{alias}"


def render_block(
    *,
    alias: str,
    hostname: str,
    port: int,
    user: str,
    identity_file: str | os.PathLike[str],
    forward_agent: bool = True,
) -> str:
    begin, end = block_markers(alias)
    lines = [
        begin,
        f"Host {host_alias(alias)}",
        f"    HostName {hostname}",
        f"    Port {port}",
        f"    User {user}",
        f"    IdentityFile {identity_file}",
        "    StrictHostKeyChecking accept-new",
        "    UserKnownHostsFile ~/.ssh/known_hosts",
    ]
    if forward_agent:
        lines.append("    ForwardAgent yes")
    lines.append(end)
    return "\n".join(lines) + "\n"


def _block_pattern(alias: str) -> re.Pattern[str]:
    begin, end = block_markers(alias)
    return re.compile(
        rf"(?:^|\n){re.escape(begin)}\n.*?\n{re.escape(end)}\n?",
        re.DOTALL,
    )


def upsert_block(
    block: str,
    *,
    alias: str,
    config_path: Path = DEFAULT_SSH_CONFIG,
) -> Path:
    """Insert or replace the alias's block. Creates the file if missing."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing = config_path.read_text() if config_path.is_file() else ""
    pattern = _block_pattern(alias)
    if pattern.search(existing):
        new_text = pattern.sub("\n" + block, existing)
    else:
        sep = "" if existing.endswith("\n") or not existing else "\n"
        new_text = existing + sep + ("\n" if existing else "") + block
    config_path.write_text(new_text)
    # SSH refuses to use a config file with overly permissive perms in some setups.
    try:
        config_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return config_path


def remove_block(alias: str, config_path: Path = DEFAULT_SSH_CONFIG) -> bool:
    """Strip the alias's block. Returns True if anything was removed."""
    if not config_path.is_file():
        return False
    text = config_path.read_text()
    pattern = _block_pattern(alias)
    if not pattern.search(text):
        return False
    new_text = pattern.sub("", text).lstrip("\n")
    config_path.write_text(new_text)
    return True
