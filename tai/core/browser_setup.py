"""Install and manage the gstack browse tool for QA automation.

Downloads the browse source from garrytan/gstack, builds the binary
with Bun, and places it where the /qa skill expects it.  The gstack
source is fetched into a temporary directory and cleaned up after the
build — only the compiled binary is kept.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from tai.core.errors import BrowserError, BunNotFoundError

_log = logging.getLogger(__name__)

BROWSE_DIR = Path.home() / ".tai" / "tools" / "browse"
BROWSE_BINARY = BROWSE_DIR / "browse"
SKILL_LINK = Path.home() / ".claude" / "skills" / "tai" / "browse"
GSTACK_REPO = "https://github.com/garrytan/gstack.git"


@dataclass(frozen=True)
class BrowserStatus:
    """Snapshot of the browse tool's installation state."""

    installed: bool
    binary_path: Path | None
    version: str | None


def check_bun() -> bool:
    """Return True when bun is available on PATH."""
    return shutil.which("bun") is not None


def check_browse_binary() -> Path | None:
    """Return the browse binary path if it exists and is executable."""
    if BROWSE_BINARY.exists() and os.access(BROWSE_BINARY, os.X_OK):
        return BROWSE_BINARY
    return None


def install_browse(ref: str = "main") -> Path:
    """Fetch gstack browse source, build the binary, and install it.

    The full gstack repo is shallow-cloned to a temp directory.  Only
    ``browse/dist/browse`` is copied out; everything else is deleted.

    Raises ``BunNotFoundError`` when Bun is missing and ``BrowserError``
    on any subprocess or filesystem failure.
    """
    if not check_bun():
        raise BunNotFoundError()

    with tempfile.TemporaryDirectory(prefix="tai-browse-") as tmpdir:
        clone_dir = Path(tmpdir) / "gstack"

        _run(
            ["git", "clone", "--depth", "1", "--single-branch",
             "-b", ref, GSTACK_REPO, str(clone_dir)],
            error_message="Failed to clone gstack repository",
        )
        _run(
            ["bun", "install"],
            cwd=clone_dir,
            error_message="bun install failed in gstack",
        )
        _run(
            ["bun", "run", "build"],
            cwd=clone_dir,
            error_message="bun run build failed in gstack",
        )

        src_binary = clone_dir / "browse" / "dist" / "browse"
        if not src_binary.exists():
            raise BrowserError(
                "Browse binary not found after build",
                hint=f"Expected at {src_binary}",
            )

        BROWSE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_binary, BROWSE_BINARY)
        BROWSE_BINARY.chmod(0o755)

    _ensure_skill_link()
    _log.info("Browse binary installed at %s", BROWSE_BINARY)
    return BROWSE_BINARY


def get_browser_status() -> BrowserStatus:
    """Aggregate installation checks into a single status object."""
    binary = check_browse_binary()
    return BrowserStatus(
        installed=binary is not None,
        binary_path=binary,
        version=_read_version() if binary else None,
    )


# ── Internal helpers ─────────────────────────────────────────────────────────


def _ensure_skill_link() -> None:
    """Create a ``dist/browse`` tree under the skill path so /qa finds it."""
    dist_dir = SKILL_LINK / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    link_target = dist_dir / "browse"
    if link_target.is_symlink() or link_target.exists():
        link_target.unlink()

    link_target.symlink_to(BROWSE_BINARY)
    _log.info("Skill link created: %s -> %s", link_target, BROWSE_BINARY)


def _read_version() -> str | None:
    """Best-effort version from the binary's --version flag."""
    try:
        result = subprocess.run(
            [str(BROWSE_BINARY), "--version"],
            capture_output=True, text=True, check=False, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        _log.debug("Could not read browse version", exc_info=True)
    return None


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    error_message: str,
) -> subprocess.CompletedProcess[str]:
    """Run a command, raising BrowserError with stderr on failure."""
    try:
        return subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise BrowserError(error_message, hint=stderr) from exc
    except FileNotFoundError as exc:
        raise BrowserError(
            error_message, hint=f"Command not found: {cmd[0]}",
        ) from exc
