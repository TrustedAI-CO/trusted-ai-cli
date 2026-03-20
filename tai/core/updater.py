"""Self-update logic: fetch latest GitHub release, detect installer, download and install."""

from __future__ import annotations

import importlib.metadata
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

import httpx
from packaging.version import Version

from tai.core.errors import TaiError

_log = logging.getLogger(__name__)

_GITHUB_REPO = "TrustedAI-CO/trusted-ai-cli"
_PACKAGE_NAME = "trusted-ai-cli"
_GITHUB_API = "https://api.github.com"
_CACHE_TTL = timedelta(hours=24)


class Installer(Enum):
    UV_TOOL = "uv-tool"
    UV = "uv"
    PIPX = "pipx"
    PIP = "pip"


class UpdateError(TaiError):
    """Raised when the update process fails."""


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int


@dataclass(frozen=True)
class ReleaseInfo:
    tag: str
    version: str
    asset: ReleaseAsset


@dataclass(frozen=True)
class UpdateCheck:
    current: str
    latest: str
    update_available: bool
    release: ReleaseInfo | None = None


def get_current_version() -> str:
    try:
        return importlib.metadata.version(_PACKAGE_NAME)
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def fetch_latest_release(
    repo: str = _GITHUB_REPO,
    *,
    client: httpx.Client | None = None,
) -> ReleaseInfo:
    """Fetch the latest GitHub release and find the wheel asset."""
    url = f"{_GITHUB_API}/repos/{repo}/releases/latest"
    owned: httpx.Client | None = None
    if client is None:
        owned = httpx.Client(timeout=15)
        client = owned

    try:
        resp = client.get(url, headers={"Accept": "application/vnd.github+json"})

        if resp.status_code == 404:
            raise UpdateError("No releases found", hint=f"Check {repo} has published releases.")
        if resp.status_code == 403:
            raise UpdateError(
                "GitHub API rate limit exceeded",
                hint="Wait a few minutes or set GITHUB_TOKEN env var.",
            )
        if resp.status_code >= 400:
            raise UpdateError(f"GitHub API error: {resp.status_code}")

        data = resp.json()
        tag = data.get("tag_name", "")
        version = tag.lstrip("v")

        assets = data.get("assets", [])
        wheel = _find_wheel_asset(assets)
        if wheel is None:
            raise UpdateError(
                "No wheel (.whl) found in latest release",
                hint=f"Release {tag} has no .whl asset to install.",
            )

        return ReleaseInfo(
            tag=tag,
            version=version,
            asset=wheel,
        )
    finally:
        if owned is not None:
            owned.close()


def _find_wheel_asset(assets: list[dict]) -> ReleaseAsset | None:
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith(".whl"):
            return ReleaseAsset(
                name=name,
                url=asset["browser_download_url"],
                size=asset["size"],
            )
    return None


def check_update(
    repo: str = _GITHUB_REPO,
    *,
    client: httpx.Client | None = None,
) -> UpdateCheck:
    """Compare current version against latest GitHub release."""
    current = get_current_version()
    release = fetch_latest_release(repo, client=client)
    current_v = Version(current)
    latest_v = Version(release.version)
    return UpdateCheck(
        current=current,
        latest=release.version,
        update_available=latest_v > current_v,
        release=release if latest_v > current_v else None,
    )


def detect_installer() -> Installer:
    """Detect which package manager installed tai.

    Heuristic: check for uv tool venv path first, then pipx, then uv pip, then pip.
    The uv tool check must come first because uv tool environments live under
    ~/.local/share/uv/tools/ and require `uv tool install` to update correctly —
    plain `uv pip install` would install into the wrong environment.
    """
    exe_path = Path(sys.executable)

    uv_tool_markers = ("uv/tools", ".local/share/uv/tools")
    if any(marker in str(exe_path) for marker in uv_tool_markers):
        if shutil.which("uv"):
            return Installer.UV_TOOL

    pipx_markers = ("pipx", ".local/pipx/venvs")
    if any(marker in str(exe_path) for marker in pipx_markers):
        if shutil.which("pipx"):
            return Installer.PIPX

    if shutil.which("uv"):
        return Installer.UV

    return Installer.PIP


def _validate_asset_name(name: str) -> str:
    """Sanitize asset name to prevent path traversal."""
    safe_name = Path(name).name
    if not safe_name or safe_name != name:
        raise UpdateError(
            "Invalid asset name in release",
            hint="Asset name must not contain path separators.",
        )
    return safe_name


def download_wheel(
    asset: ReleaseAsset,
    dest_dir: Path | None = None,
    *,
    client: httpx.Client | None = None,
) -> Path:
    """Download a wheel asset and verify its size."""
    safe_name = _validate_asset_name(asset.name)

    if dest_dir is None:
        dest_dir = Path(tempfile.mkdtemp(prefix="tai-update-"))

    dest = dest_dir / safe_name
    owned: httpx.Client | None = None
    if client is None:
        owned = httpx.Client(timeout=60, follow_redirects=True)
        client = owned

    try:
        with client.stream("GET", asset.url) as resp:
            if resp.status_code >= 400:
                raise UpdateError(
                    f"Failed to download wheel: HTTP {resp.status_code}",
                    hint="Check your network connection and try again.",
                )
            with dest.open("wb") as fh:
                for chunk in resp.iter_bytes(chunk_size=65536):
                    fh.write(chunk)

        if dest.stat().st_size != asset.size:
            actual_size = dest.stat().st_size
            dest.unlink(missing_ok=True)
            raise UpdateError(
                f"Downloaded file size mismatch: expected {asset.size}, got {actual_size}",
                hint="Download may be corrupt. Try again.",
            )

        return dest
    finally:
        if owned is not None:
            owned.close()


def install_wheel(wheel_path: Path, installer: Installer) -> None:
    """Install a wheel using the detected package manager."""
    cmd = _build_install_cmd(installer, wheel_path)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise UpdateError(
            f"Install failed ({installer.value}): {stderr[:200]}",
            hint=f"Try manually: {' '.join(str(c) for c in cmd)}",
        )


def _build_install_cmd(installer: Installer, wheel_path: Path) -> list[str]:
    match installer:
        case Installer.UV_TOOL:
            return ["uv", "tool", "install", "--force", str(wheel_path)]
        case Installer.UV:
            return ["uv", "pip", "install", "--force-reinstall", str(wheel_path)]
        case Installer.PIPX:
            return ["pipx", "install", "--force", str(wheel_path)]
        case Installer.PIP:
            return [sys.executable, "-m", "pip", "install", "--force-reinstall", str(wheel_path)]
        case _:
            raise UpdateError(f"Unsupported installer: {installer!r}")


def run_post_update() -> tuple[bool, bool, bool]:
    """Run setup-skills, setup-hooks, and setup-templates via subprocess.

    Returns (skills_ok, hooks_ok, templates_ok).
    """
    tai_bin = shutil.which("tai") or "tai"

    try:
        skills_result = subprocess.run(
            [tai_bin, "claude", "setup-skills", "--force"],
            capture_output=True,
            text=True,
        )
        skills_ok = skills_result.returncode == 0
    except OSError as exc:
        _log.debug("Post-update setup-skills failed: %s", exc)
        skills_ok = False

    try:
        hooks_result = subprocess.run(
            [tai_bin, "claude", "setup-hooks"],
            capture_output=True,
            text=True,
        )
        hooks_ok = hooks_result.returncode == 0
    except OSError as exc:
        _log.debug("Post-update setup-hooks failed: %s", exc)
        hooks_ok = False

    try:
        templates_result = subprocess.run(
            [tai_bin, "pdf", "setup-templates", "--force"],
            capture_output=True,
            text=True,
        )
        templates_ok = templates_result.returncode == 0
    except OSError as exc:
        _log.debug("Post-update setup-templates failed: %s", exc)
        templates_ok = False

    return skills_ok, hooks_ok, templates_ok


# ── Startup update-check cache ───────────────────────────────────────────────


def _cache_path() -> Path:
    return Path.home() / ".config" / "tai" / "update-check.json"


def load_cached_update() -> UpdateCheck | None:
    """Load cached update check if still fresh (within 24h)."""
    path = _cache_path()
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
        checked_at = datetime.fromisoformat(data["checked_at"])
        if datetime.now(timezone.utc) - checked_at > _CACHE_TTL:
            return None
        return UpdateCheck(
            current=data["current"],
            latest=data["latest"],
            update_available=data["update_available"],
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def save_update_cache(info: UpdateCheck) -> None:
    """Persist update check result for startup banner (best-effort)."""
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "current": info.current,
            "latest": info.latest,
            "update_available": info.update_available,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }))
    except OSError:
        pass  # cache is best-effort; do not fail the update


def clear_update_cache() -> None:
    """Remove cached update check (after successful update)."""
    path = _cache_path()
    path.unlink(missing_ok=True)
