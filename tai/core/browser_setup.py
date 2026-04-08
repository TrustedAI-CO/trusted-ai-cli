"""Install and manage the gstack browse tool for QA automation.

Downloads gstack, builds the browse binary with Bun, and copies the
full browse directory (source + dist + node_modules) to ~/.tai/tools/browse/.
The browse binary is a thin CLI client that spawns a Bun server process,
so it needs the source tree and dependencies at runtime.
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
BROWSE_BINARY = BROWSE_DIR / "dist" / "browse"
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
    """Fetch gstack, build the browse tool, and install it.

    The full gstack repo is shallow-cloned to a temp directory.  The
    ``browse/`` subtree (source, dist, node_modules) is copied to
    ``~/.tai/tools/browse/`` so the server can run at runtime.  The rest
    of gstack is discarded.

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

        src_browse = clone_dir / "browse"
        src_binary = src_browse / "dist" / "browse"
        if not src_binary.exists():
            raise BrowserError(
                "Browse binary not found after build",
                hint=f"Expected at {src_binary}",
            )

        # Copy the full browse/ tree (src + dist + node_modules).
        # The binary is a thin CLI; it needs server.ts + playwright at runtime.
        if BROWSE_DIR.exists():
            shutil.rmtree(BROWSE_DIR)
        BROWSE_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_browse, BROWSE_DIR)

        # Also copy node_modules from the gstack root (playwright lives there)
        src_modules = clone_dir / "node_modules"
        dst_modules = BROWSE_DIR / "node_modules"
        if src_modules.exists() and not dst_modules.exists():
            shutil.copytree(src_modules, dst_modules)

    _ensure_skill_link()
    _log.info("Browse tool installed at %s", BROWSE_DIR)
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
    """Symlink the skill path to BROWSE_DIR so /qa finds the binary."""
    SKILL_LINK.parent.mkdir(parents=True, exist_ok=True)

    if SKILL_LINK.is_symlink() or SKILL_LINK.exists():
        if SKILL_LINK.is_symlink():
            SKILL_LINK.unlink()
        else:
            shutil.rmtree(SKILL_LINK)

    SKILL_LINK.symlink_to(BROWSE_DIR)
    _log.info("Skill link created: %s -> %s", SKILL_LINK, BROWSE_DIR)


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
