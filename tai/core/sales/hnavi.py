"""Hnavi (発注ナビ) sales platform client."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tai.core.sales.browser import SalesBrowser, get_credentials

if TYPE_CHECKING:
    from playwright.sync_api import Page


@dataclass
class HnaviJob:
    """A job listing on Hnavi."""

    id: str
    title: str
    budget: str | None = None
    deadline: str | None = None
    tags: list[str] | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "budget": self.budget,
            "deadline": self.deadline,
            "tags": self.tags or [],
            "url": self.url,
        }


@dataclass
class HnaviNegotiation:
    """An active negotiation on Hnavi."""

    id: str
    title: str
    company: str | None = None
    status: str | None = None
    last_message_date: str | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "status": self.status,
            "last_message_date": self.last_message_date,
            "url": self.url,
        }


@dataclass
class HnaviMessage:
    """A message in a negotiation."""

    sender: str
    content: str
    date: str | None = None

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "content": self.content,
            "date": self.date,
        }


class HnaviClient:
    """Client for interacting with Hnavi (発注ナビ) developer portal."""

    BASE_URL = "https://developer.hnavi.co.jp"

    def __init__(self, browser: SalesBrowser, email: str | None = None, password: str | None = None):
        """Initialize Hnavi client.

        Args:
            browser: SalesBrowser instance
            email: Login email (or set HNAVI_EMAIL env var)
            password: Login password (or set HNAVI_PASSWORD env var)
        """
        self.browser = browser
        if email and password:
            self.email = email
            self.password = password
        else:
            self.email, self.password = get_credentials("hnavi")
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
        if self.browser.load_session("hnavi"):
            self.page.goto(self.BASE_URL)
            # Check if we're actually logged in
            if "/sign_in" not in self.page.url:
                self._logged_in = True
                return

        # Need to login
        self.login()

    def login(self) -> None:
        """Login to Hnavi and establish session."""
        self.page.goto(f"{self.BASE_URL}/developer_users/sign_in")
        self.page.wait_for_load_state("networkidle")

        # Fill login form
        self.page.fill('input[name="developer_user[email]"]', self.email)
        self.page.fill('input[name="developer_user[password]"]', self.password)
        self.page.click('input[type="submit"]')

        # Wait for redirect after login
        self.page.wait_for_load_state("networkidle")

        if "/sign_in" in self.page.url:
            raise RuntimeError("Hnavi login failed. Check credentials.")

        # Save session for future use
        self.browser.save_session(self.page, "hnavi")
        self._logged_in = True

    def list_jobs(self, category: str | None = None, include_saas: bool = False) -> list[HnaviJob]:
        """List available jobs, optionally filtered by category.

        Args:
            category: Filter by category tag (e.g., "システム", "ホームページ", "動画制作")
                     If None, returns all jobs.
            include_saas: If True, also fetch jobs from the SaaS tab

        Returns:
            List of job listings
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.BASE_URL}/jobs")
        self.page.wait_for_load_state("networkidle")

        jobs = self._parse_job_cards(category)

        # Also fetch SaaS jobs if requested
        if include_saas:
            self.page.goto(f"{self.BASE_URL}/jobs?saas=saas")
            self.page.wait_for_load_state("networkidle")
            jobs.extend(self._parse_job_cards(category))

        return jobs

    def _parse_job_cards(self, category: str | None = None) -> list[HnaviJob]:
        """Parse job cards from the current page.

        Args:
            category: Optional category filter

        Returns:
            List of HnaviJob objects
        """
        jobs = []

        # Job cards are in div.card.mb-4.shadow containers
        job_cards = self.page.query_selector_all("div.card.mb-4.shadow.position-relative")

        for card in job_cards:
            try:
                # Extract job URL ID from the card-body link
                link = card.query_selector("a.link-dark.card-body")
                if not link:
                    continue

                href = link.get_attribute("href") or ""
                match = re.search(r"/jobs/(\d+)", href)
                if not match:
                    continue

                url_id = match.group(1)

                # Extract the display No. (e.g., "No. 202604030016")
                no_elem = card.query_selector("div.ms-3")
                display_no = None
                if no_elem:
                    no_text = no_elem.inner_text().strip()
                    no_match = re.search(r"No\.\s*(\d+)", no_text)
                    if no_match:
                        display_no = no_match.group(1)

                # Extract title from div.title
                title_elem = card.query_selector("div.title")
                title = title_elem.inner_text().strip() if title_elem else ""

                # Extract category tag (e.g., システム, ホームページ)
                tag_elem = card.query_selector("span.badge.me-2")
                tag = tag_elem.inner_text().strip() if tag_elem else None

                # Filter by category if specified
                if category and tag != category:
                    continue

                # Extract deadline from text-danger div (e.g., "〆 2026年4月6日 17:00")
                deadline = None
                deadline_elem = card.query_selector("div.text-danger")
                if deadline_elem:
                    deadline_text = deadline_elem.inner_text().strip()
                    # Remove the 〆 prefix
                    deadline = deadline_text.replace("〆", "").strip()

                jobs.append(
                    HnaviJob(
                        id=display_no or url_id,
                        title=title,
                        budget=None,  # Budget not shown on list page
                        deadline=deadline,
                        tags=[tag] if tag else [],
                        url=f"{self.BASE_URL}/jobs/{url_id}",
                    )
                )
            except Exception:
                continue

        return jobs

    def get_job(self, job_id: str) -> dict:
        """Get detailed information about a job.

        Args:
            job_id: The job ID

        Returns:
            Dict with job details
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.BASE_URL}/jobs/{job_id}")
        self.page.wait_for_load_state("networkidle")

        # Extract all visible text content from the main content area
        content = {}

        # Get title
        title_elem = self.page.query_selector("h1, .job-title, [class*='title']")
        if title_elem:
            content["title"] = title_elem.inner_text().strip()

        # Get the main content
        main_elem = self.page.query_selector("main, .content, .job-detail, article")
        if main_elem:
            content["description"] = main_elem.inner_text().strip()

        content["id"] = job_id
        content["url"] = f"{self.BASE_URL}/jobs/{job_id}"

        return content

    def list_negotiations(self) -> list[HnaviNegotiation]:
        """List active negotiations.

        Returns:
            List of negotiations
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.BASE_URL}/negotiations")
        self.page.wait_for_load_state("networkidle")

        negotiations = []

        # Find negotiation items
        neg_elements = self.page.query_selector_all(
            ".negotiation-item, .negotiation-card, [class*='negotiation'], tr[data-id]"
        )

        for elem in neg_elements:
            try:
                # Extract negotiation ID from link
                link = elem.query_selector("a[href*='/negotiations/']")
                if not link:
                    continue

                href = link.get_attribute("href") or ""
                match = re.search(r"/negotiations/(\d+)", href)
                if not match:
                    continue

                neg_id = match.group(1)
                title = link.inner_text().strip()

                # Extract company name
                company = None
                company_elem = elem.query_selector("[class*='company'], [class*='client']")
                if company_elem:
                    company = company_elem.inner_text().strip()

                # Extract status
                status = None
                status_elem = elem.query_selector("[class*='status'], .badge")
                if status_elem:
                    status = status_elem.inner_text().strip()

                # Extract last message date
                date = None
                date_elem = elem.query_selector("[class*='date'], time")
                if date_elem:
                    date = date_elem.inner_text().strip()

                negotiations.append(
                    HnaviNegotiation(
                        id=neg_id,
                        title=title,
                        company=company,
                        status=status,
                        last_message_date=date,
                        url=f"{self.BASE_URL}/negotiations/{neg_id}",
                    )
                )
            except Exception:
                continue

        return negotiations

    def get_negotiation(self, neg_id: str) -> dict:
        """Get negotiation details including messages.

        Args:
            neg_id: Negotiation ID

        Returns:
            Dict with negotiation details and messages
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.BASE_URL}/negotiations/{neg_id}")
        self.page.wait_for_load_state("networkidle")

        result = {
            "id": neg_id,
            "url": f"{self.BASE_URL}/negotiations/{neg_id}",
            "messages": [],
        }

        # Get title/project name
        title_elem = self.page.query_selector("h1, .negotiation-title, [class*='title']")
        if title_elem:
            result["title"] = title_elem.inner_text().strip()

        # Get company info
        company_elem = self.page.query_selector("[class*='company'], [class*='client']")
        if company_elem:
            result["company"] = company_elem.inner_text().strip()

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
                        HnaviMessage(sender=sender, content=content, date=date).to_dict()
                    )
            except Exception:
                continue

        return result

    def send_message(self, neg_id: str, message: str, file_path: str | None = None) -> bool:
        """Send a message in a negotiation.

        Args:
            neg_id: Negotiation ID
            message: Message content
            file_path: Optional file to attach

        Returns:
            True if message was sent successfully
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.BASE_URL}/negotiations/{neg_id}")
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
