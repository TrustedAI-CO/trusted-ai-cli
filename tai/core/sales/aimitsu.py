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
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

        # Fill login form
        self.page.fill('input[name="email"], input[type="email"]', self.email)
        self.page.fill('input[name="password"], input[type="password"]', self.password)
        self.page.click('button[type="submit"], input[type="submit"]')

        # Wait for redirect after login
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

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
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)  # Wait for Vue components to render

        projects = []

        # Page uses PrimeVue .p-card components
        cards = self.page.query_selector_all(".p-card")

        for card in cards:
            try:
                # Look for project link
                link = card.query_selector('a[href*="/competitions/"]')
                if not link:
                    continue

                href = link.get_attribute("href") or ""
                match = re.search(r"/competitions/(\d+)", href)
                if not match:
                    continue

                project_no = match.group(1)

                # Extract status from card header
                status = None
                status_elem = card.query_selector(".p-card-header .flex-grow-1")
                if status_elem:
                    status = status_elem.inner_text().strip()

                # Extract title and customer from card text
                card_text = card.inner_text()

                # Title appears after "案件"
                title = ""
                title_match = re.search(r"案件\s*\n(.+)", card_text)
                if title_match:
                    title = title_match.group(1).strip()

                # Customer info appears after "カスタマー情報"
                customer = None
                customer_match = re.search(r"カスタマー情報\s*\n(.+?)\n(.+)", card_text)
                if customer_match:
                    customer = f"{customer_match.group(1).strip()} {customer_match.group(2).strip()}"

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
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

        result: dict = {
            "no": project_no,
            "url": f"{self.MYPAGE_URL}/competitions/{project_no}",
            "messages": [],
        }

        # Get page text for regex extraction
        body = self.page.query_selector("body")
        page_text = body.inner_text() if body else ""

        # Extract customer name from "〇〇様 とのメッセージ"
        customer_match = re.search(r"(.+?様)\s*とのメッセージ", page_text)
        if customer_match:
            result["customer"] = customer_match.group(1).strip()

        # Extract 依頼日 (request date)
        date_match = re.search(r"依頼日[：:]\s*(\d+年\d+月\d+日)", page_text)
        if date_match:
            result["request_date"] = date_match.group(1)

        # Extract お問い合わせNo. (inquiry number)
        inquiry_match = re.search(r"お問い合わせNo\.?\s*[：:]\s*(\d+)", page_text)
        if inquiry_match:
            result["inquiry_no"] = inquiry_match.group(1)

        # Extract project details from dt/dd pairs
        dt_dd_map: dict[str, str] = {}
        dts = self.page.query_selector_all("dt")
        for dt in dts:
            label = dt.inner_text().strip()
            dd = dt.evaluate_handle("(el) => el.nextElementSibling")
            if dd:
                dd_elem = dd.as_element()
                if dd_elem:
                    tag = dd_elem.evaluate("(el) => el.tagName")
                    if tag == "DD":
                        value = dd_elem.inner_text().strip()
                        dt_dd_map[label] = value

        # Map dt/dd values to result fields
        field_mapping = {
            "案件タイトル": "title",
            "発注の背景": "background",
            "発注の詳細": "details",
            "システム詳細": "system_details",
            "必須機能": "required_features",
            "利用ユーザー（ターゲット）": "target_users",
            "現状の課題と理由": "current_issues",
            "予算": "budget",
            "予算確度": "budget_certainty",
            "予算レベル": "budget_level",
            "納期": "delivery",
            "スケジュール": "schedule",
            "見積もり時期": "estimate_timing",
            "開発": "development_type",
            "開発種別": "development_category",
            "打ち合わせ方法": "meeting_method",
            "連絡可能な時間": "contact_hours",
        }

        for dt_label, result_key in field_mapping.items():
            if dt_label in dt_dd_map:
                result[result_key] = dt_dd_map[dt_label]

        # Extract requirements from card bodies (fallback)
        card_bodies = self.page.query_selector_all(".p-card-body, .p-card-content")
        for card_body in card_bodies:
            text = card_body.inner_text().strip()
            if not text or "message" in text.lower():
                continue

            # Parse 必須条件 (requirements) if not already set
            if "必須条件" in text and "requirements" not in result:
                req_match = re.search(r"必須条件\s*\n(.+?)(?:\n|$)", text)
                if req_match:
                    result["requirements"] = req_match.group(1).strip()

            # Parse アピールしてほしいポイント (appeal points)
            if "アピールしてほしいポイント" in text and "appeal_points" not in result:
                appeal_match = re.search(
                    r"アピールしてほしいポイント\s*\n(.+?)(?:\n|$)", text
                )
                if appeal_match:
                    result["appeal_points"] = appeal_match.group(1).strip()

            # Parse 商談希望日 (preferred meeting times)
            if "商談希望日" in text and "preferred_times" not in result:
                meeting_match = re.search(r"商談希望日[：:]\s*\n?(.+)", text, re.DOTALL)
                if meeting_match:
                    result["preferred_times"] = meeting_match.group(1).strip()

        # Get messages from .message-box elements
        seen_contents: set[str] = set()
        message_boxes = self.page.query_selector_all(".message-box")

        for box in message_boxes:
            try:
                # Get header with sender and date
                header = box.query_selector(".header")

                # Extract company and person name from spans (first two font-bold elements)
                sender = "Unknown"
                if header:
                    font_bolds = header.query_selector_all(".font-bold")
                    # Filter out status indicators like "既読" (read)
                    parts = [
                        fb.inner_text().strip()
                        for fb in font_bolds[:2]  # Only first two (company, person)
                        if fb.inner_text().strip() not in ("既読", "未読")
                    ]
                    sender = " ".join(parts) if parts else "Unknown"

                # Extract date from .text-time span
                date = None
                if header:
                    date_elem = header.query_selector(".text-time")
                    date = date_elem.inner_text().strip() if date_elem else None

                # Get message content
                msg_elem = box.query_selector(".message")
                content = msg_elem.inner_text().strip() if msg_elem else ""

                # Deduplicate messages
                content_key = content[:100] if content else ""
                if content and content_key not in seen_contents:
                    seen_contents.add(content_key)
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
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)

        # Find PrimeVue textarea (no name attribute, uses classes)
        textarea = self.page.query_selector(
            'textarea.p-inputtextarea, textarea[placeholder*="メッセージ"]'
        )
        if not textarea:
            raise RuntimeError("Could not find message input field")

        textarea.fill(message)

        # Attach file if specified
        if file_path:
            file_input = self.page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(file_path)

        # Wait for send button to be enabled (Vue reactivity)
        self.page.wait_for_timeout(500)

        # Find send button by Japanese text or class
        submit_btn = self.page.query_selector(
            'button.btn-f-blue:not(.p-disabled), '
            'button:has-text("メッセージを送信する"):not(.p-disabled)'
        )
        if not submit_btn:
            # Try without the :not(.p-disabled) in case button is still disabled
            submit_btn = self.page.query_selector(
                'button.btn-f-blue, button:has-text("メッセージを送信する")'
            )
            if not submit_btn:
                raise RuntimeError("Could not find submit button")

        submit_btn.click()

        # Wait for confirmation dialog to appear
        self.page.wait_for_timeout(500)

        # Find and click confirm button in the dialog
        confirm_btn = self.page.query_selector(
            '.p-dialog button.btn-blue, '
            '.p-dialog button:has-text("送信する")'
        )
        if confirm_btn:
            confirm_btn.click()
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1000)
        else:
            raise RuntimeError("Could not find confirmation button in dialog")

        return True
