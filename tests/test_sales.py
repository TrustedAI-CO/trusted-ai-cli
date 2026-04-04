"""Tests for tai.core.sales module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── browser.py tests ─────────────────────────────────────────────────────────


def test_get_credentials_from_env():
    """Get credentials from environment variables."""
    from tai.core.sales.browser import get_credentials

    with patch.dict("os.environ", {"TEST_EMAIL": "test@example.com", "TEST_PASSWORD": "secret"}):
        email, password = get_credentials("test")
        assert email == "test@example.com"
        assert password == "secret"


def test_get_credentials_missing():
    """Error when credentials are missing."""
    from tai.core.sales.browser import get_credentials

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="Missing credentials"):
            get_credentials("test")


def test_get_credentials_partial():
    """Error when only email is set."""
    from tai.core.sales.browser import get_credentials

    with patch.dict("os.environ", {"TEST_EMAIL": "test@example.com"}, clear=True):
        with pytest.raises(ValueError, match="Missing credentials"):
            get_credentials("test")


def test_save_cookies(tmp_path):
    """Save cookies to file."""
    from tai.core.sales.browser import save_cookies

    mock_page = MagicMock()
    mock_page.context.cookies.return_value = [{"name": "session", "value": "abc123"}]

    with patch("tai.core.sales.browser.SESSIONS_DIR", tmp_path):
        save_cookies(mock_page, "test")

    cookie_file = tmp_path / "test_cookies.json"
    assert cookie_file.exists()
    cookies = json.loads(cookie_file.read_text())
    assert len(cookies) == 1
    assert cookies[0]["name"] == "session"


def test_load_cookies_exists(tmp_path):
    """Load cookies from existing file."""
    from tai.core.sales.browser import load_cookies

    cookie_file = tmp_path / "test_cookies.json"
    cookie_file.write_text(json.dumps([{"name": "session", "value": "abc123"}]))

    mock_context = MagicMock()

    with patch("tai.core.sales.browser.SESSIONS_DIR", tmp_path):
        result = load_cookies(mock_context, "test")

    assert result is True
    mock_context.add_cookies.assert_called_once()


def test_load_cookies_not_exists(tmp_path):
    """Return False when cookie file doesn't exist."""
    from tai.core.sales.browser import load_cookies

    mock_context = MagicMock()

    with patch("tai.core.sales.browser.SESSIONS_DIR", tmp_path):
        result = load_cookies(mock_context, "nonexistent")

    assert result is False
    mock_context.add_cookies.assert_not_called()


def test_load_cookies_invalid_json(tmp_path):
    """Return False when cookie file has invalid JSON."""
    from tai.core.sales.browser import load_cookies

    cookie_file = tmp_path / "test_cookies.json"
    cookie_file.write_text("invalid json")

    mock_context = MagicMock()

    with patch("tai.core.sales.browser.SESSIONS_DIR", tmp_path):
        result = load_cookies(mock_context, "test")

    assert result is False


def test_clear_cookies(tmp_path):
    """Clear cookies removes file."""
    from tai.core.sales.browser import clear_cookies

    cookie_file = tmp_path / "test_cookies.json"
    cookie_file.write_text("{}")

    with patch("tai.core.sales.browser.SESSIONS_DIR", tmp_path):
        clear_cookies("test")

    assert not cookie_file.exists()


def test_clear_cookies_not_exists(tmp_path):
    """Clear cookies is no-op when file doesn't exist."""
    from tai.core.sales.browser import clear_cookies

    with patch("tai.core.sales.browser.SESSIONS_DIR", tmp_path):
        # Should not raise
        clear_cookies("nonexistent")


# ── SalesBrowser class tests ─────────────────────────────────────────────────

# Check if playwright is available
try:
    import playwright  # noqa: F401

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

requires_playwright = pytest.mark.skipif(
    not HAS_PLAYWRIGHT, reason="playwright not installed"
)


@requires_playwright
def test_sales_browser_context_manager():
    """SalesBrowser works as context manager."""
    from tai.core.sales.browser import SalesBrowser

    mock_pw_instance = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_pw_instance.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_pw_instance

        with SalesBrowser() as browser:
            assert browser._browser is mock_browser
            assert browser._context is mock_context

        # Verify cleanup
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_pw_instance.stop.assert_called_once()


@requires_playwright
def test_sales_browser_new_page():
    """SalesBrowser.new_page creates a page."""
    from tai.core.sales.browser import SalesBrowser

    mock_pw_instance = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_pw_instance.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_pw_instance

        with SalesBrowser() as browser:
            page = browser.new_page()
            assert page is mock_page


@requires_playwright
def test_sales_browser_context_property_error():
    """SalesBrowser.context raises when not started."""
    from tai.core.sales.browser import SalesBrowser

    browser = SalesBrowser()
    with pytest.raises(RuntimeError, match="Browser not started"):
        _ = browser.context


@requires_playwright
def test_sales_browser_headless_option():
    """SalesBrowser respects headless option."""
    from tai.core.sales.browser import SalesBrowser

    mock_pw_instance = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_pw_instance.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_pw_instance

        with SalesBrowser(headless=False):
            pass

        mock_pw_instance.chromium.launch.assert_called_once_with(headless=False)


@requires_playwright
def test_sales_browser_load_session():
    """SalesBrowser.load_session delegates to load_cookies."""
    from tai.core.sales.browser import SalesBrowser

    mock_pw_instance = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_pw_instance.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_pw_instance

        with patch("tai.core.sales.browser.load_cookies", return_value=True) as mock_load:
            with SalesBrowser() as browser:
                result = browser.load_session("test")
                assert result is True
                mock_load.assert_called_once_with(mock_context, "test")


@requires_playwright
def test_sales_browser_save_session():
    """SalesBrowser.save_session delegates to save_cookies."""
    from tai.core.sales.browser import SalesBrowser

    mock_pw_instance = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_pw_instance.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_pw_instance

        with patch("tai.core.sales.browser.save_cookies") as mock_save:
            with SalesBrowser() as browser:
                browser.save_session(mock_page, "test")
                mock_save.assert_called_once_with(mock_page, "test")


# ── HnaviJob dataclass tests ─────────────────────────────────────────────────


def test_hnavi_job_to_dict():
    """HnaviJob.to_dict returns correct structure."""
    from tai.core.sales.hnavi import HnaviJob

    job = HnaviJob(
        id="123",
        title="AI Development",
        budget="500万円",
        deadline="2026-05-01",
        tags=["AI", "ML"],
        url="https://example.com/jobs/123",
    )

    d = job.to_dict()
    assert d["id"] == "123"
    assert d["title"] == "AI Development"
    assert d["budget"] == "500万円"
    assert d["deadline"] == "2026-05-01"
    assert d["tags"] == ["AI", "ML"]
    assert d["url"] == "https://example.com/jobs/123"


def test_hnavi_job_to_dict_defaults():
    """HnaviJob.to_dict handles None values."""
    from tai.core.sales.hnavi import HnaviJob

    job = HnaviJob(id="123", title="Test")

    d = job.to_dict()
    assert d["budget"] is None
    assert d["deadline"] is None
    assert d["tags"] == []


def test_hnavi_negotiation_to_dict():
    """HnaviNegotiation.to_dict returns correct structure."""
    from tai.core.sales.hnavi import HnaviNegotiation

    neg = HnaviNegotiation(
        id="456",
        title="Project X",
        company="ABC Corp",
        status="進行中",
        last_message_date="2026-04-01",
        url="https://example.com/negotiations/456",
    )

    d = neg.to_dict()
    assert d["id"] == "456"
    assert d["title"] == "Project X"
    assert d["company"] == "ABC Corp"
    assert d["status"] == "進行中"


def test_hnavi_message_to_dict():
    """HnaviMessage.to_dict returns correct structure."""
    from tai.core.sales.hnavi import HnaviMessage

    msg = HnaviMessage(sender="User", content="Hello!", date="2026-04-01")

    d = msg.to_dict()
    assert d["sender"] == "User"
    assert d["content"] == "Hello!"
    assert d["date"] == "2026-04-01"


# ── AimitsuProject dataclass tests ───────────────────────────────────────────


def test_aimitsu_project_to_dict():
    """AimitsuProject.to_dict returns correct structure."""
    from tai.core.sales.aimitsu import AimitsuProject

    proj = AimitsuProject(
        no="12345",
        title="Web Development",
        customer="XYZ Inc",
        status="商談中",
        url="https://example.com/competitions/12345",
    )

    d = proj.to_dict()
    assert d["no"] == "12345"
    assert d["title"] == "Web Development"
    assert d["customer"] == "XYZ Inc"
    assert d["status"] == "商談中"


def test_aimitsu_message_to_dict():
    """AimitsuMessage.to_dict returns correct structure."""
    from tai.core.sales.aimitsu import AimitsuMessage

    msg = AimitsuMessage(sender="Supplier", content="Thanks!", date="2026-04-01")

    d = msg.to_dict()
    assert d["sender"] == "Supplier"
    assert d["content"] == "Thanks!"
    assert d["date"] == "2026-04-01"


# ── HnaviClient tests ────────────────────────────────────────────────────────


def test_hnavi_client_init_with_credentials():
    """HnaviClient can be initialized with explicit credentials."""
    from tai.core.sales.hnavi import HnaviClient

    mock_browser = MagicMock()
    client = HnaviClient(mock_browser, email="test@example.com", password="secret")

    assert client.email == "test@example.com"
    assert client.password == "secret"


def test_hnavi_client_init_from_env():
    """HnaviClient gets credentials from environment."""
    from tai.core.sales.hnavi import HnaviClient

    mock_browser = MagicMock()

    with patch.dict("os.environ", {"HNAVI_EMAIL": "env@example.com", "HNAVI_PASSWORD": "envsecret"}):
        client = HnaviClient(mock_browser)

    assert client.email == "env@example.com"
    assert client.password == "envsecret"


def test_hnavi_client_page_property():
    """HnaviClient.page creates page on first access."""
    from tai.core.sales.hnavi import HnaviClient

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page

    with patch.dict("os.environ", {"HNAVI_EMAIL": "test@example.com", "HNAVI_PASSWORD": "secret"}):
        client = HnaviClient(mock_browser)
        page = client.page

    assert page is mock_page
    mock_browser.new_page.assert_called_once()


# ── AimitsuClient tests ──────────────────────────────────────────────────────


def test_aimitsu_client_init_with_credentials():
    """AimitsuClient can be initialized with explicit credentials."""
    from tai.core.sales.aimitsu import AimitsuClient

    mock_browser = MagicMock()
    client = AimitsuClient(mock_browser, email="test@example.com", password="secret")

    assert client.email == "test@example.com"
    assert client.password == "secret"


def test_aimitsu_client_init_from_env():
    """AimitsuClient gets credentials from environment."""
    from tai.core.sales.aimitsu import AimitsuClient

    mock_browser = MagicMock()

    with patch.dict("os.environ", {"AIMITSU_EMAIL": "env@example.com", "AIMITSU_PASSWORD": "envsecret"}):
        client = AimitsuClient(mock_browser)

    assert client.email == "env@example.com"
    assert client.password == "envsecret"


def test_aimitsu_client_page_property():
    """AimitsuClient.page creates page on first access."""
    from tai.core.sales.aimitsu import AimitsuClient

    mock_browser = MagicMock()
    mock_page = MagicMock()
    mock_browser.new_page.return_value = mock_page

    with patch.dict("os.environ", {"AIMITSU_EMAIL": "test@example.com", "AIMITSU_PASSWORD": "secret"}):
        client = AimitsuClient(mock_browser)
        page = client.page

    assert page is mock_page
    mock_browser.new_page.assert_called_once()
