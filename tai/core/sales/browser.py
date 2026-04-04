"""Shared browser automation utilities for sales platforms."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from tai.core.config import CONFIG_DIR

# Load .env file from current directory
load_dotenv()

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page

SESSIONS_DIR = CONFIG_DIR / "sales_sessions"


def get_credentials(platform: str) -> tuple[str, str]:
    """Get credentials for a sales platform from environment variables.

    Args:
        platform: Platform name (hnavi, aimitsu)

    Returns:
        Tuple of (email, password)

    Raises:
        ValueError: If credentials are not found
    """
    email_key = f"{platform.upper()}_EMAIL"
    pass_key = f"{platform.upper()}_PASSWORD"

    email = os.getenv(email_key)
    password = os.getenv(pass_key)

    if not email or not password:
        raise ValueError(
            f"Missing credentials for {platform}. "
            f"Set {email_key} and {pass_key} environment variables."
        )

    return email, password


def save_cookies(page: Page, platform: str) -> None:
    """Save browser cookies for a platform session.

    Args:
        page: Playwright page with active session
        platform: Platform name (hnavi, aimitsu)
    """
    cookies = page.context.cookies()
    path = SESSIONS_DIR / f"{platform}_cookies.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cookies, indent=2))


def load_cookies(context: BrowserContext, platform: str) -> bool:
    """Load cached cookies for a platform session.

    Args:
        context: Playwright browser context
        platform: Platform name (hnavi, aimitsu)

    Returns:
        True if cookies were loaded, False otherwise
    """
    path = SESSIONS_DIR / f"{platform}_cookies.json"
    if path.exists():
        try:
            cookies = json.loads(path.read_text())
            context.add_cookies(cookies)
            return True
        except (json.JSONDecodeError, OSError):
            return False
    return False


def clear_cookies(platform: str) -> None:
    """Clear cached cookies for a platform.

    Args:
        platform: Platform name (hnavi, aimitsu)
    """
    path = SESSIONS_DIR / f"{platform}_cookies.json"
    if path.exists():
        path.unlink()


class SalesBrowser:
    """Manages authenticated browser sessions for sales platforms.

    Usage:
        with SalesBrowser() as browser:
            page = browser.new_page()
            # ... automation code
    """

    def __init__(self, headless: bool = True):
        """Initialize browser manager.

        Args:
            headless: Run browser in headless mode (default True)
        """
        self.headless = headless
        self._playwright = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "SalesBrowser":
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        return self

    def __exit__(self, *args) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    @property
    def context(self) -> "BrowserContext":
        """Get the browser context."""
        if self._context is None:
            raise RuntimeError("Browser not started. Use 'with SalesBrowser() as browser:'")
        return self._context

    def new_page(self) -> "Page":
        """Create a new browser page."""
        return self.context.new_page()

    def load_session(self, platform: str) -> bool:
        """Load cached session for a platform.

        Args:
            platform: Platform name (hnavi, aimitsu)

        Returns:
            True if session was loaded
        """
        return load_cookies(self.context, platform)

    def save_session(self, page: "Page", platform: str) -> None:
        """Save current session for a platform.

        Args:
            page: Page with active session
            platform: Platform name (hnavi, aimitsu)
        """
        save_cookies(page, platform)
