"""Aimitsu (アイミツ) sales platform client."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tai.core.sales.browser import SalesBrowser, get_credentials

if TYPE_CHECKING:
    from playwright.sync_api import Page


@dataclass
class AimitsuProject:
    """A project listing on Aimitsu."""

    no: str  # 案件No.
    title: str
    customer: str | None = None  # カスタマー情報
    status: str | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        return {
            "no": self.no,
            "title": self.title,
            "customer": self.customer,
            "status": self.status,
            "url": self.url,
        }


@dataclass
class AimitsuMessage:
    """A message in a project."""

    sender: str
    content: str
    date: str | None = None

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "content": self.content,
            "date": self.date,
        }


class AimitsuClient:
    """Client for interacting with Aimitsu (アイミツ/PRONI) supplier portal."""

    BASE_URL = "https://imitsu.jp"
    MYPAGE_URL = "https://imitsu.jp/mypage/supplier"

    def __init__(self, browser: SalesBrowser, email: str | None = None, password: str | None = None):
        """Initialize Aimitsu client.

        Args:
            browser: SalesBrowser instance
            email: Login email (or set AIMITSU_EMAIL env var)
            password: Login password (or set AIMITSU_PASSWORD env var)
        """
        self.browser = browser
        if email and password:
            self.email = email
            self.password = password
        else:
            self.email, self.password = get_credentials("aimitsu")
        self._page: Page | None = None
        self._logged_in = False

    @property
    def page(self) -> "Page":
        """Get or create the browser page."""
        if self._page is None:
            self._page = self.browser.new_page()
        return self._page

    def _ensure_logged_in(self) -> None:
        """Ensure we're logged in, attempting cached session first."""
        if self._logged_in:
            return

        # Try loading cached session
        if self.browser.load_session("aimitsu"):
            self.page.goto(self.MYPAGE_URL)
            # Check if we're actually logged in (not redirected to login)
            if "/login" not in self.page.url and "/sign_in" not in self.page.url:
                self._logged_in = True
                return

        # Need to login
        self.login()

    def login(self) -> None:
        """Login to Aimitsu and establish session."""
        self.page.goto(f"{self.BASE_URL}/login")
        self.page.wait_for_load_state("networkidle")

        # Fill login form
        self.page.fill('input[name="email"], input[type="email"]', self.email)
        self.page.fill('input[name="password"], input[type="password"]', self.password)
        self.page.click('button[type="submit"], input[type="submit"]')

        # Wait for redirect after login
        self.page.wait_for_load_state("networkidle")

        if "/login" in self.page.url:
            raise RuntimeError("Aimitsu login failed. Check credentials.")

        # Save session for future use
        self.browser.save_session(self.page, "aimitsu")
        self._logged_in = True

    def list_projects(self) -> list[AimitsuProject]:
        """List projects in negotiation.

        Returns:
            List of projects
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.MYPAGE_URL}/competition-list/in_negotiation_appointment")
        self.page.wait_for_load_state("networkidle")

        projects = []

        # Find project rows in table
        rows = self.page.query_selector_all("table tr, .project-item, [class*='competition']")

        for row in rows:
            try:
                # Look for project link
                link = row.query_selector("a[href*='/competitions/']")
                if not link:
                    continue

                href = link.get_attribute("href") or ""
                match = re.search(r"/competitions/(\d+)", href)
                if not match:
                    continue

                project_no = match.group(1)
                title = link.inner_text().strip()

                # Extract customer info
                customer = None
                customer_elem = row.query_selector("[class*='customer'], td:first-child")
                if customer_elem:
                    customer = customer_elem.inner_text().strip()

                # Extract status
                status = None
                status_elem = row.query_selector("[class*='status'], .badge")
                if status_elem:
                    status = status_elem.inner_text().strip()

                projects.append(
                    AimitsuProject(
                        no=project_no,
                        title=title,
                        customer=customer,
                        status=status,
                        url=f"{self.MYPAGE_URL}/competitions/{project_no}",
                    )
                )
            except Exception:
                continue

        return projects

    def get_project(self, project_no: str) -> dict:
        """Get detailed information about a project.

        Args:
            project_no: The project number (案件No.)

        Returns:
            Dict with project details and messages
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.MYPAGE_URL}/competitions/{project_no}")
        self.page.wait_for_load_state("networkidle")

        result = {
            "no": project_no,
            "url": f"{self.MYPAGE_URL}/competitions/{project_no}",
            "messages": [],
        }

        # Get title
        title_elem = self.page.query_selector("h1, .project-title, [class*='title']")
        if title_elem:
            result["title"] = title_elem.inner_text().strip()

        # Get customer info
        customer_elem = self.page.query_selector("[class*='customer'], [class*='client']")
        if customer_elem:
            result["customer"] = customer_elem.inner_text().strip()

        # Get main content/description
        content_elem = self.page.query_selector("main, .content, .project-detail, article")
        if content_elem:
            result["description"] = content_elem.inner_text().strip()

        # Get messages
        message_elements = self.page.query_selector_all(
            ".message, .message-item, [class*='message'], .chat-item"
        )

        for msg_elem in message_elements:
            try:
                # Get sender
                sender_elem = msg_elem.query_selector("[class*='sender'], [class*='author'], .name")
                sender = sender_elem.inner_text().strip() if sender_elem else "Unknown"

                # Get content
                content_elem = msg_elem.query_selector("[class*='content'], [class*='body'], p")
                content = content_elem.inner_text().strip() if content_elem else ""

                # Get date
                date_elem = msg_elem.query_selector("[class*='date'], time, .timestamp")
                date = date_elem.inner_text().strip() if date_elem else None

                if content:
                    result["messages"].append(
                        AimitsuMessage(sender=sender, content=content, date=date).to_dict()
                    )
            except Exception:
                continue

        return result

    def send_message(self, project_no: str, message: str, file_path: str | None = None) -> bool:
        """Send a message in a project.

        Args:
            project_no: Project number (案件No.)
            message: Message content
            file_path: Optional file to attach

        Returns:
            True if message was sent successfully
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.MYPAGE_URL}/competitions/{project_no}")
        self.page.wait_for_load_state("networkidle")

        # Find and fill message textarea
        textarea = self.page.query_selector(
            'textarea[name*="message"], textarea[name*="body"], textarea.message-input'
        )
        if not textarea:
            raise RuntimeError("Could not find message input field")

        textarea.fill(message)

        # Attach file if specified
        if file_path:
            file_input = self.page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(file_path)

        # Submit the message
        submit_btn = self.page.query_selector(
            'button[type="submit"], input[type="submit"], .send-button, [class*="submit"]'
        )
        if not submit_btn:
            raise RuntimeError("Could not find submit button")

        submit_btn.click()
        self.page.wait_for_load_state("networkidle")

        return True
