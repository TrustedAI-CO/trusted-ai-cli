"""Unit tests for tai.core.updater — GitHub release fetching, version comparison, installer detection."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import pytest

from tai.core.updater import (
    Installer,
    ReleaseAsset,
    UpdateCheck,
    UpdateError,
    _find_wheel_asset,
    check_update,
    clear_update_cache,
    detect_installer,
    download_wheel,
    fetch_latest_release,
    install_wheel,
    load_cached_update,
    save_update_cache,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

WHEEL_NAME = "trusted_ai_cli-0.3.0-py3-none-any.whl"
WHEEL_CONTENT = b"PK\x03\x04fake-wheel-bytes-1234567890"

RELEASE_JSON = {
    "tag_name": "v0.3.0",
    "assets": [
        {
            "name": WHEEL_NAME,
            "browser_download_url": f"https://github.com/TrustedAI-CO/trusted-ai-cli/releases/download/v0.3.0/{WHEEL_NAME}",
            "size": len(WHEEL_CONTENT),
        },
    ],
}


def _mock_client(responses: list[httpx.Response]) -> httpx.Client:
    """Build an httpx.Client that returns canned responses in order."""
    transport = httpx.MockTransport(lambda req: responses.pop(0))
    return httpx.Client(transport=transport)


# ── fetch_latest_release ──────────────────────────────────────────────────────


def test_fetch_latest_release_success():
    client = _mock_client([httpx.Response(200, json=RELEASE_JSON)])
    result = fetch_latest_release(client=client)

    assert result.tag == "v0.3.0"
    assert result.version == "0.3.0"
    assert result.asset.name == WHEEL_NAME


def test_fetch_latest_release_no_releases():
    client = _mock_client([httpx.Response(404, json={"message": "Not Found"})])

    with pytest.raises(UpdateError, match="No releases found"):
        fetch_latest_release(client=client)


def test_fetch_latest_release_rate_limited():
    client = _mock_client([httpx.Response(403, json={"message": "rate limit"})])

    with pytest.raises(UpdateError, match="rate limit"):
        fetch_latest_release(client=client)


def test_fetch_latest_release_no_wheel_asset():
    release_no_wheel = {
        "tag_name": "v0.3.0",
        "assets": [{"name": "source.tar.gz", "browser_download_url": "https://x", "size": 100}],
    }
    client = _mock_client([httpx.Response(200, json=release_no_wheel)])

    with pytest.raises(UpdateError, match="No wheel"):
        fetch_latest_release(client=client)


def test_fetch_latest_release_server_error():
    client = _mock_client([httpx.Response(500, text="Internal Server Error")])

    with pytest.raises(UpdateError, match="500"):
        fetch_latest_release(client=client)


# ── _find_wheel_asset ─────────────────────────────────────────────────────────


def test_find_wheel_asset_returns_match():
    assets = [
        {"name": "source.tar.gz", "browser_download_url": "https://x", "size": 100},
        {"name": WHEEL_NAME, "browser_download_url": "https://y", "size": 200},
    ]
    result = _find_wheel_asset(assets)
    assert result is not None
    assert result.name == WHEEL_NAME


def test_find_wheel_asset_returns_none():
    assets = [{"name": "source.tar.gz", "browser_download_url": "https://x", "size": 100}]
    assert _find_wheel_asset(assets) is None


# ── check_update ──────────────────────────────────────────────────────────────


def test_check_update_available():
    client = _mock_client([httpx.Response(200, json=RELEASE_JSON)])

    with patch("tai.core.updater.get_current_version", return_value="0.2.0"):
        result = check_update(client=client)

    assert result.update_available is True
    assert result.current == "0.2.0"
    assert result.latest == "0.3.0"
    assert result.release is not None


def test_check_update_already_current():
    client = _mock_client([httpx.Response(200, json=RELEASE_JSON)])

    with patch("tai.core.updater.get_current_version", return_value="0.3.0"):
        result = check_update(client=client)

    assert result.update_available is False
    assert result.release is None


# ── detect_installer ──────────────────────────────────────────────────────────


def test_detect_installer_uv_tool(tmp_path):
    uv_tool_python = tmp_path / ".local" / "share" / "uv" / "tools" / "tai" / "bin" / "python"
    uv_tool_python.parent.mkdir(parents=True)
    uv_tool_python.touch()

    with patch("shutil.which", side_effect=lambda cmd: "/usr/bin/uv" if cmd == "uv" else None), \
         patch("tai.core.updater.sys") as mock_sys:
        mock_sys.executable = str(uv_tool_python)
        result = detect_installer()

    assert result == Installer.UV_TOOL


def test_detect_installer_uv(tmp_path):
    with patch("shutil.which", side_effect=lambda cmd: "/usr/bin/uv" if cmd == "uv" else None), \
         patch("tai.core.updater.sys") as mock_sys:
        mock_sys.executable = str(tmp_path / "python")
        result = detect_installer()

    assert result == Installer.UV


def test_detect_installer_pipx(tmp_path):
    pipx_python = tmp_path / ".local" / "pipx" / "venvs" / "tai" / "bin" / "python"
    pipx_python.parent.mkdir(parents=True)
    pipx_python.touch()

    with patch("tai.core.updater.sys") as mock_sys, \
         patch("shutil.which", side_effect=lambda cmd: "/usr/bin/pipx" if cmd == "pipx" else None):
        mock_sys.executable = str(pipx_python)
        result = detect_installer()

    assert result == Installer.PIPX


def test_detect_installer_pip_fallback():
    with patch("shutil.which", return_value=None), \
         patch("tai.core.updater.sys") as mock_sys:
        mock_sys.executable = "/usr/bin/python3"
        result = detect_installer()

    assert result == Installer.PIP


# ── download_wheel ────────────────────────────────────────────────────────────


def test_download_wheel_success(tmp_path):
    asset = ReleaseAsset(name=WHEEL_NAME, url="https://x/wheel.whl", size=len(WHEEL_CONTENT))
    transport = httpx.MockTransport(lambda req: httpx.Response(200, content=WHEEL_CONTENT))
    client = httpx.Client(transport=transport)

    path = download_wheel(asset, dest_dir=tmp_path, client=client)

    assert path.exists()
    assert path.read_bytes() == WHEEL_CONTENT


def test_download_wheel_size_mismatch(tmp_path):
    asset = ReleaseAsset(name=WHEEL_NAME, url="https://x/wheel.whl", size=9999)
    transport = httpx.MockTransport(lambda req: httpx.Response(200, content=WHEEL_CONTENT))
    client = httpx.Client(transport=transport)

    with pytest.raises(UpdateError, match="size mismatch"):
        download_wheel(asset, dest_dir=tmp_path, client=client)


def test_download_wheel_http_error(tmp_path):
    asset = ReleaseAsset(name=WHEEL_NAME, url="https://x/wheel.whl", size=100)
    transport = httpx.MockTransport(lambda req: httpx.Response(404, text="Not Found"))
    client = httpx.Client(transport=transport)

    with pytest.raises(UpdateError, match="Failed to download"):
        download_wheel(asset, dest_dir=tmp_path, client=client)


def test_download_wheel_rejects_path_traversal(tmp_path):
    asset = ReleaseAsset(name="../evil.whl", url="https://x/evil.whl", size=100)
    transport = httpx.MockTransport(lambda req: httpx.Response(200, content=b"data"))
    client = httpx.Client(transport=transport)

    with pytest.raises(UpdateError, match="Invalid asset name"):
        download_wheel(asset, dest_dir=tmp_path, client=client)


# ── install_wheel ─────────────────────────────────────────────────────────────


def test_install_wheel_success(tmp_path):
    wheel = tmp_path / WHEEL_NAME
    wheel.write_bytes(WHEEL_CONTENT)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        install_wheel(wheel, Installer.PIP)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "--force-reinstall" in cmd
    assert str(wheel) in cmd


def test_install_wheel_failure(tmp_path):
    wheel = tmp_path / WHEEL_NAME
    wheel.write_bytes(WHEEL_CONTENT)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Permission denied"
        mock_run.return_value.stdout = ""
        with pytest.raises(UpdateError, match="Install failed"):
            install_wheel(wheel, Installer.UV)


def test_install_wheel_uv_tool(tmp_path):
    wheel = tmp_path / WHEEL_NAME
    wheel.write_bytes(WHEEL_CONTENT)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        install_wheel(wheel, Installer.UV_TOOL)

    cmd = mock_run.call_args[0][0]
    assert cmd[:3] == ["uv", "tool", "install"]
    assert "--force" in cmd
    assert str(wheel) in cmd


def test_install_wheel_pipx_uses_pipx(tmp_path):
    wheel = tmp_path / WHEEL_NAME
    wheel.write_bytes(WHEEL_CONTENT)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        install_wheel(wheel, Installer.PIPX)

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "pipx"


# ── Update cache ──────────────────────────────────────────────────────────────


def test_save_and_load_cache(tmp_path):
    cache_file = tmp_path / "update-check.json"

    with patch("tai.core.updater._cache_path", return_value=cache_file):
        info = UpdateCheck(current="0.2.0", latest="0.3.0", update_available=True)
        save_update_cache(info)

        loaded = load_cached_update()

    assert loaded is not None
    assert loaded.update_available is True
    assert loaded.latest == "0.3.0"


def test_load_cache_expired(tmp_path):
    cache_file = tmp_path / "update-check.json"
    old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    cache_file.write_text(json.dumps({
        "current": "0.2.0",
        "latest": "0.3.0",
        "update_available": True,
        "checked_at": old_time,
    }))

    with patch("tai.core.updater._cache_path", return_value=cache_file):
        assert load_cached_update() is None


def test_load_cache_missing(tmp_path):
    cache_file = tmp_path / "nonexistent.json"

    with patch("tai.core.updater._cache_path", return_value=cache_file):
        assert load_cached_update() is None


def test_load_cache_corrupt(tmp_path):
    cache_file = tmp_path / "update-check.json"
    cache_file.write_text("not json")

    with patch("tai.core.updater._cache_path", return_value=cache_file):
        assert load_cached_update() is None


def test_clear_cache(tmp_path):
    cache_file = tmp_path / "update-check.json"
    cache_file.write_text("{}")

    with patch("tai.core.updater._cache_path", return_value=cache_file):
        clear_update_cache()

    assert not cache_file.exists()
