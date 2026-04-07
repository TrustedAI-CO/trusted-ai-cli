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


@dataclass
class HnaviEntryQuestion:
    """An entry requirement question."""

    index: int
    question: str
    requirement_id: str
    required: bool = True

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "question": self.question,
            "requirement_id": self.requirement_id,
            "required": self.required,
        }


@dataclass
class HnaviTeamMember:
    """A team member for entry."""

    id: str
    name: str
    selected: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "selected": self.selected,
        }


@dataclass
class HnaviEntryForm:
    """Entry form structure."""

    job_id: str
    job_title: str
    questions: list[HnaviEntryQuestion]
    team_members: list[HnaviTeamMember]
    default_url: str | None = None

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "questions": [q.to_dict() for q in self.questions],
            "team_members": [m.to_dict() for m in self.team_members],
            "default_url": self.default_url,
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
            job_id: The job ID (URL ID like 15995, or display No. like 202604020007)

        Returns:
            Dict with job details
        """
        self._ensure_logged_in()
        self.page.goto(f"{self.BASE_URL}/jobs/{job_id}")
        self.page.wait_for_load_state("networkidle")

        # Detect "Not Found" pages
        not_found = self.page.query_selector("div.fs-3.fw-bold")
        if not_found and "Not Found" in not_found.inner_text():
            raise RuntimeError(f"Job {job_id} not found. Check the ID — negotiation IDs are different from job IDs.")

        content: dict = {
            "url_id": job_id,
            "url": f"{self.BASE_URL}/jobs/{job_id}",
        }

        # Get display No. (e.g., "No. 202604020007")
        no_elem = self.page.query_selector("div.ms-3")
        if no_elem:
            no_text = no_elem.inner_text().strip()
            no_match = re.search(r"No\.\s*(\d+)", no_text)
            if no_match:
                content["no"] = no_match.group(1)

        # Get status badge (募集中, etc.)
        status_elem = self.page.query_selector("div.badge.min-w-140px")
        if status_elem:
            content["status"] = status_elem.inner_text().strip()

        # Get deadline (〆 2026年4月6日 14:30)
        deadline_elem = self.page.query_selector("div.text-danger")
        if deadline_elem:
            deadline_text = deadline_elem.inner_text().strip()
            content["deadline"] = deadline_text.replace("〆", "").strip()

        # Get category tag (AI, システム, etc.)
        tag_elem = self.page.query_selector("span.badge.me-2")
        if tag_elem:
            content["category"] = tag_elem.inner_text().strip()

        # Get title
        title_elem = self.page.query_selector("div.title")
        if title_elem:
            content["title"] = title_elem.inner_text().strip()

        # Get max companies (上限企業数: 10社)
        max_companies_section = self.page.query_selector("div.bg-light.text-secondary.fw-bold.py-1.px-3")
        if max_companies_section and "上限企業数" in max_companies_section.inner_text():
            parent = max_companies_section.evaluate_handle("el => el.parentElement")
            if parent:
                text = parent.inner_text().strip()
                # Extract the number after "上限企業数"
                match = re.search(r"上限企業数\s*(\d+社)", text)
                if match:
                    content["max_companies"] = match.group(1)

        # Get company info cards (会社規模, 会社拠点, 企業HPの有無)
        info_cards = self.page.query_selector_all("div.card.shadow.h-100 div.text-center")
        for card in info_cards:
            try:
                label_elem = card.query_selector("div.fw-bold")
                value_elem = card.query_selector("div:not(.fw-bold)")
                if label_elem and value_elem:
                    label = label_elem.inner_text().strip()
                    value = value_elem.inner_text().strip()
                    if label == "会社規模":
                        content["company_size"] = value
                    elif label == "会社拠点":
                        content["company_location"] = value
                    elif label == "企業HPの有無":
                        content["has_website"] = value
            except Exception:
                continue

        # Get entry conditions (エントリー条件)
        conditions = []
        condition_items = self.page.query_selector_all("div.pre-wrap.text-break.w-100")
        for item in condition_items:
            text = item.inner_text().strip()
            if text:
                conditions.append(text)
        if conditions:
            content["entry_conditions"] = conditions

        # Get all labeled sections (bg-light headers with next sibling content)
        all_headers = self.page.query_selector_all(
            "div.fw-bold.mb-2.bg-light.text-secondary.py-1.px-3, "
            "div.fw-bold.mt-4.mb-2.bg-light.text-secondary.py-1.px-3"
        )
        header_map = {
            "お問い合わせ時の内容": "inquiry_content",
            "発注ナビ担当者のヒアリング内容": "hearing_content",
            "予算": "budget",
            "納期": "delivery",
            "カテゴリ": None,  # already extracted above
        }
        for header in all_headers:
            try:
                header_text = header.inner_text().strip()
                field = header_map.get(header_text)
                if field is None:
                    continue
                # Try next sibling; if empty, try the one after (some sections
                # have an empty <div></div> spacer between header and content)
                text = ""
                sibling = header.evaluate_handle("el => el.nextElementSibling")
                if sibling:
                    text = sibling.inner_text().strip()
                if not text:
                    sibling = header.evaluate_handle(
                        "el => el.nextElementSibling?.nextElementSibling"
                    )
                    if sibling:
                        text = sibling.inner_text().strip()
                if text:
                    content[field] = text
            except Exception:
                continue

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

        # Cards use the same structure as job listings
        cards = self.page.query_selector_all("div.card.mb-4.shadow.position-relative")

        for card in cards:
            try:
                # Extract negotiation ID from the card-body link
                link = card.query_selector("a.link-dark.card-body")
                if not link:
                    continue

                href = link.get_attribute("href") or ""
                match = re.search(r"/negotiations/(\d+)", href)
                if not match:
                    continue

                neg_id = match.group(1)

                # Extract title from div.title
                title_elem = card.query_selector("div.title")
                title = title_elem.inner_text().strip() if title_elem else ""

                # Extract company name from card content (社名：xxx)
                company = None
                card_text = card.inner_text()
                company_match = re.search(r"社名：(.+?)(?:\n|$)", card_text)
                if company_match:
                    company = company_match.group(1).strip()

                # Extract status badge (コンタクト中, etc.)
                status = None
                status_elem = card.query_selector("div.badge.min-w-140px")
                if status_elem:
                    status = status_elem.inner_text().strip()

                # Extract introduction date (紹介日時：xxx)
                date = None
                date_elem = card.query_selector("div.text-primary")
                if date_elem:
                    date_text = date_elem.inner_text().strip()
                    date = date_text.replace("紹介日時：", "").strip()

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

        result: dict = {
            "id": neg_id,
            "url": f"{self.BASE_URL}/negotiations/{neg_id}",
            "messages": [],
        }

        # Get status badge (コンタクト中, 商談中, etc.)
        status_elem = self.page.query_selector("div.fs-3.fw-bold + div.badge")
        if status_elem:
            result["status"] = status_elem.inner_text().strip()

        # Get title and No. from the job link
        job_link = self.page.query_selector(f'a[href="/negotiations/{neg_id}/job"]')
        if job_link:
            link_text = job_link.inner_text().strip()
            # Format: "AIを活用した...（202601090010）"
            title_match = re.match(r"(.+?)（(\d+)）", link_text)
            if title_match:
                result["title"] = title_match.group(1).strip()
                result["no"] = title_match.group(2)
            else:
                result["title"] = link_text

        # Get company info from the card body
        card_body = self.page.query_selector("div.card.mt-4 div.card-body")
        if card_body:
            card_text = card_body.inner_text()
            info_patterns = {
                "company": r"会社名：(.+?)(?:\n|$)",
                "contact_person": r"発注者名：(.+?)(?:\n|$)",
                "company_address": r"会社住所：(.+?)(?:\n|$)",
                "email": r"メールアドレス：(.+?)(?:\n|$)",
                "phone": r"電話番号：(.+?)(?:\n|$)",
            }
            for field, pattern in info_patterns.items():
                match = re.search(pattern, card_text)
                if match:
                    result[field] = match.group(1).strip()

            # Get plan info
            plan_match = re.search(r"本案件の利用プラン：(.+?)(?:\n|$)", card_text)
            if plan_match:
                result["plan"] = plan_match.group(1).strip()

        # Get self introduction text
        self_intro_elem = self.page.query_selector("div.untruncated.pre-wrap")
        if not self_intro_elem:
            self_intro_elem = self.page.query_selector("div.truncated.pre-wrap")
        if self_intro_elem:
            text = self_intro_elem.inner_text().strip()
            # Remove "もっと見る" / "少なく表示する" links
            text = re.sub(r"(もっと見る|少なく表示する)\s*$", "", text).strip()
            if text:
                result["self_introduction"] = text

        # Get assigned member
        member_elem = self.page.query_selector(
            "div.fw-bold:has-text('担当者') + div + div.pre-wrap"
        )
        if not member_elem:
            # Fallback: find by looking for text after 担当者 heading
            body_text = card_body.inner_text() if card_body else ""
            member_match = re.search(r"の担当者\n.+\n(.+?)(?:\n|$)", body_text)
            if member_match:
                result["assigned_member"] = member_match.group(1).strip()

        # Get messages from div.negotiation-messages
        msg_container = self.page.query_selector("div.negotiation-messages")
        if msg_container:
            # Each message block: header (d-flex) + content (mt-2)
            # Messages are separated by <hr>
            headers = msg_container.query_selector_all(
                "div.d-flex.align-items-center.flex-wrap"
            )
            for header in headers:
                try:
                    # Extract sender name and company from fw-bold elements
                    bolds = header.query_selector_all("div.fw-bold.pe-2")
                    parts = [b.inner_text().strip() for b in bolds]

                    sender = ""
                    date = None
                    if len(parts) >= 3:
                        sender = f"{parts[1]} {parts[0]}"  # Company + Name
                        date = parts[2]
                    elif len(parts) >= 2:
                        sender = parts[0]
                        date = parts[1]
                    elif parts:
                        sender = parts[0]

                    # Get read status
                    badge = header.query_selector("div.badge.rounded-pill")
                    read_status = badge.inner_text().strip() if badge else None

                    # Get message content from next sibling div.mt-2
                    content_div = header.evaluate_handle(
                        "el => el.nextElementSibling"
                    )
                    content = ""
                    if content_div:
                        # Check for deleted message
                        deleted = content_div.query_selector("div.text-secondary")
                        if deleted and "削除されました" in deleted.inner_text():
                            continue
                        # Get actual content from pre-wrap div
                        pre_wrap = content_div.query_selector("div.pre-wrap")
                        if pre_wrap:
                            content = pre_wrap.inner_text().strip()

                    if content:
                        msg = HnaviMessage(
                            sender=sender, content=content, date=date
                        ).to_dict()
                        if read_status:
                            msg["read_status"] = read_status
                        result["messages"].append(msg)
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
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)  # Brief wait for dynamic content

        # Find and fill message textarea (specific selector for negotiation messages)
        textarea = self.page.query_selector('textarea[name="negotiation_message[content]"]')
        if not textarea:
            raise RuntimeError("Could not find message input field")

        textarea.fill(message)

        # Attach file if specified
        if file_path:
            file_input = self.page.query_selector('input[type="file"]')
            if file_input:
                file_input.set_input_files(file_path)

        # Submit the form via JavaScript (button click fails due to overlapping elements)
        form = self.page.query_selector('form[action="/negotiation_messages"]')
        if not form:
            raise RuntimeError("Could not find message form")

        self.page.evaluate('document.querySelector(\'form[action="/negotiation_messages"]\').submit()')
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

        return True

    def get_entry_form(self, job_id: str) -> HnaviEntryForm:
        """Get the entry form structure for a job.

        Args:
            job_id: The job ID (URL ID or display No.)

        Returns:
            HnaviEntryForm with questions and team members
        """
        self._ensure_logged_in()

        # Navigate to job page
        self.page.goto(f"{self.BASE_URL}/jobs/{job_id}")
        self.page.wait_for_load_state("networkidle")

        # Get job title
        title_elem = self.page.query_selector("div.title")
        job_title = title_elem.inner_text().strip() if title_elem else ""

        # Click the entry button to go to entry form
        entry_btn = self.page.query_selector('input[data-go-to-entry="true"]')
        if not entry_btn:
            raise RuntimeError(
                "Entry button not found. Job may be closed or already entered."
            )

        entry_btn.click()
        self.page.wait_for_load_state("networkidle")

        # Parse questions
        questions: list[HnaviEntryQuestion] = []
        form_groups = self.page.query_selector_all(
            "div.form-group.text.required.entry_entry_requirement_answers_answer"
        )

        for i, group in enumerate(form_groups):
            label = group.query_selector("label")
            textarea = group.query_selector("textarea")

            if label and textarea:
                question_text = label.inner_text().strip()
                # Remove the * indicator
                question_text = question_text.replace(" *", "").strip()

                # Get requirement ID from the hidden input that follows
                name = textarea.get_attribute("name") or ""
                req_id_match = re.search(r"\[(\d+)\]\[answer\]", name)
                idx = int(req_id_match.group(1)) if req_id_match else i

                # Find the hidden requirement_id input
                req_id_input = self.page.query_selector(
                    f'input[name="entry[entry_requirement_answers_attributes][{idx}][entry_requirement_id]"]'
                )
                req_id = req_id_input.get_attribute("value") if req_id_input else str(idx)

                questions.append(
                    HnaviEntryQuestion(
                        index=idx,
                        question=question_text,
                        requirement_id=req_id,
                        required="required" in (label.get_attribute("class") or ""),
                    )
                )

        # Parse team members
        team_members: list[HnaviTeamMember] = []
        member_checkboxes = self.page.query_selector_all(
            'input[name="entry[developer_user_ids][]"][type="checkbox"]'
        )

        for cb in member_checkboxes:
            member_id = cb.get_attribute("value")
            if not member_id:
                continue

            cb_id = cb.get_attribute("id") or ""
            label = self.page.query_selector(f'label[for="{cb_id}"]')
            name = label.inner_text().strip() if label else f"Member {member_id}"
            selected = cb.get_attribute("checked") is not None

            team_members.append(
                HnaviTeamMember(id=member_id, name=name, selected=selected)
            )

        # Get default URL
        url_input = self.page.query_selector('input[name="entry[url]"]')
        default_url = url_input.get_attribute("value") if url_input else None

        return HnaviEntryForm(
            job_id=job_id,
            job_title=job_title,
            questions=questions,
            team_members=team_members,
            default_url=default_url,
        )

    def submit_entry(
        self,
        job_id: str,
        answers: list[str],
        self_introduction: str,
        team_member_ids: list[str] | None = None,
        url: str | None = None,
        file_path: str | None = None,
    ) -> bool:
        """Submit an entry for a job.

        Args:
            job_id: The job ID
            answers: List of answers to entry questions (in order)
            self_introduction: Self-introduction text
            team_member_ids: List of team member IDs to include (default: first available)
            url: URL to display (default: use pre-filled)
            file_path: Optional file to attach

        Returns:
            True if entry was submitted successfully
        """
        self._ensure_logged_in()

        # Navigate to job page
        self.page.goto(f"{self.BASE_URL}/jobs/{job_id}")
        self.page.wait_for_load_state("networkidle")

        # Click the entry button
        entry_btn = self.page.query_selector('input[data-go-to-entry="true"]')
        if not entry_btn:
            raise RuntimeError(
                "Entry button not found. Job may be closed or already entered."
            )

        entry_btn.click()
        self.page.wait_for_load_state("networkidle")

        # Fill in answers
        textareas = self.page.query_selector_all(
            'textarea[name*="entry_requirement_answers_attributes"]'
        )

        for i, textarea in enumerate(textareas):
            if i < len(answers):
                textarea.fill(answers[i])

        # Fill self introduction
        self_intro_textarea = self.page.query_selector(
            'textarea[name="entry[self_introduction]"]'
        )
        if self_intro_textarea:
            self_intro_textarea.fill(self_introduction)

        # Select team members
        if team_member_ids:
            # Uncheck all first
            member_checkboxes = self.page.query_selector_all(
                'input[name="entry[developer_user_ids][]"][type="checkbox"]'
            )
            for cb in member_checkboxes:
                if cb.is_checked():
                    cb.uncheck()

            # Check specified members
            for member_id in team_member_ids:
                cb = self.page.query_selector(
                    f'input[name="entry[developer_user_ids][]"][value="{member_id}"]'
                )
                if cb:
                    cb.check()

        # Set URL if specified
        if url:
            url_input = self.page.query_selector('input[name="entry[url]"]')
            if url_input:
                url_input.fill(url)

        # Attach file if specified
        if file_path:
            file_input = self.page.query_selector('input[name="entry[files][]"]')
            if file_input:
                file_input.set_input_files(file_path)

        # Submit the entry
        submit_btn = self.page.query_selector(
            'input[type="submit"][name="commit"][value="エントリー"]'
        )
        if not submit_btn:
            raise RuntimeError("Submit button not found")

        submit_btn.click()
        self.page.wait_for_load_state("networkidle")

        # Check if we're redirected away from the entry form (success)
        if "/entries/new" in self.page.url:
            raise RuntimeError("Entry submission may have failed. Still on entry form.")

        return True
