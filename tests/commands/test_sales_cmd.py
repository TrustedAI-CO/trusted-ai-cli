"""Tests for tai sales commands."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from tai.commands.sales import app

runner = CliRunner()


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_playwright():
    """Mock playwright to avoid actual browser automation."""
    with patch("tai.commands.sales._check_playwright"):
        yield


@pytest.fixture
def mock_hnavi_client():
    """Mock HnaviClient for testing."""
    with patch("tai.core.sales.HnaviClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_aimitsu_client():
    """Mock AimitsuClient for testing."""
    with patch("tai.core.sales.AimitsuClient") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_browser():
    """Mock SalesBrowser context manager."""
    with patch("tai.core.sales.SalesBrowser") as mock_cls:
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_cls.return_value = mock_browser
        yield mock_browser


# ── playwright check tests ───────────────────────────────────────────────────


def test_sales_no_playwright():
    """Error when playwright is not installed."""
    with patch.dict("sys.modules", {"playwright": None}):
        with patch("tai.commands.sales._check_playwright") as mock_check:
            mock_check.side_effect = SystemExit(1)
            result = runner.invoke(app, ["status"])
    # Should fail because _check_playwright raises
    assert result.exit_code != 0


def test_help_shows_subcommands():
    """Sales help shows available subcommands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "hnavi" in result.output
    assert "aimitsu" in result.output
    assert "status" in result.output
    assert "login" in result.output


# ── hnavi subcommand tests ───────────────────────────────────────────────────


def test_hnavi_help():
    """Hnavi help shows available commands."""
    result = runner.invoke(app, ["hnavi", "--help"])
    assert result.exit_code == 0
    assert "jobs" in result.output
    assert "active" in result.output
    assert "send" in result.output


def test_hnavi_jobs_list(mock_playwright):
    """List hnavi jobs returns table."""
    from tai.core.sales.hnavi import HnaviJob

    mock_jobs = [
        HnaviJob(id="123", title="AI Development", budget="500万円", tags=["AI"]),
        HnaviJob(id="456", title="ML Project", budget="300万円", tags=["AI", "ML"]),
    ]

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.list_jobs.return_value = mock_jobs
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["hnavi", "jobs"])

    assert result.exit_code == 0
    assert "123" in result.output
    assert "AI Development" in result.output


def test_hnavi_jobs_json(mock_playwright):
    """List hnavi jobs with --json returns JSON."""
    from tai.core.sales.hnavi import HnaviJob

    mock_jobs = [
        HnaviJob(id="123", title="AI Development", budget="500万円", tags=["AI"]),
    ]

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.list_jobs.return_value = mock_jobs
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["hnavi", "jobs", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "123"


def test_hnavi_jobs_empty(mock_playwright):
    """Empty job list shows message."""
    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.list_jobs.return_value = []
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["hnavi", "jobs"])

    assert result.exit_code == 0
    assert "No jobs found" in result.output


def test_hnavi_active_list(mock_playwright):
    """List active negotiations."""
    from tai.core.sales.hnavi import HnaviNegotiation

    mock_negotiations = [
        HnaviNegotiation(id="789", title="Project X", company="ABC Corp", status="進行中"),
    ]

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.list_negotiations.return_value = mock_negotiations
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["hnavi", "active"])

    assert result.exit_code == 0
    assert "789" in result.output
    assert "Project X" in result.output


def test_hnavi_send_message(mock_playwright):
    """Send message to negotiation."""
    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.send_message.return_value = True
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["hnavi", "send", "123", "Hello!"])

    assert result.exit_code == 0
    assert "Message sent" in result.output
    mock_client.send_message.assert_called_once_with("123", "Hello!", None)


def test_hnavi_send_file_not_found(mock_playwright):
    """Error when file to attach doesn't exist."""
    result = runner.invoke(app, ["hnavi", "send", "123", "Hello!", "--file", "/nonexistent/file.pdf"])
    assert result.exit_code != 0
    assert "File not found" in result.output


# ── aimitsu subcommand tests ─────────────────────────────────────────────────


def test_aimitsu_help():
    """Aimitsu help shows available commands."""
    result = runner.invoke(app, ["aimitsu", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "show" in result.output
    assert "send" in result.output


def test_aimitsu_list(mock_playwright):
    """List aimitsu projects."""
    from tai.core.sales.aimitsu import AimitsuProject

    mock_projects = [
        AimitsuProject(no="12345", title="Web Development", customer="XYZ Inc", status="商談中"),
    ]

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.AimitsuClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.list_projects.return_value = mock_projects
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["aimitsu", "list"])

    assert result.exit_code == 0
    assert "12345" in result.output
    assert "Web Development" in result.output


def test_aimitsu_list_json(mock_playwright):
    """List aimitsu projects with --json."""
    from tai.core.sales.aimitsu import AimitsuProject

    mock_projects = [
        AimitsuProject(no="12345", title="Web Development", customer="XYZ Inc"),
    ]

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.AimitsuClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.list_projects.return_value = mock_projects
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["aimitsu", "list", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["no"] == "12345"


def test_aimitsu_show(mock_playwright):
    """Show aimitsu project details."""
    mock_project = {
        "no": "12345",
        "title": "Web Development",
        "customer": "XYZ Inc",
        "url": "https://imitsu.jp/mypage/supplier/competitions/12345",
        "messages": [],
    }

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.AimitsuClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.get_project.return_value = mock_project
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["aimitsu", "show", "12345"])

    assert result.exit_code == 0
    assert "Web Development" in result.output
    assert "XYZ Inc" in result.output


def test_aimitsu_send_message(mock_playwright):
    """Send message to aimitsu project."""
    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.AimitsuClient") as mock_client_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_client = MagicMock()
        mock_client.send_message.return_value = True
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, ["aimitsu", "send", "12345", "Hello!"])

    assert result.exit_code == 0
    assert "Message sent" in result.output


# ── login command tests ──────────────────────────────────────────────────────


def test_login_success(mock_playwright):
    """Test login to both platforms."""
    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_hnavi_cls,
        patch("tai.core.sales.AimitsuClient") as mock_aimitsu_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_hnavi = MagicMock()
        mock_hnavi.login.return_value = None
        mock_hnavi_cls.return_value = mock_hnavi

        mock_aimitsu = MagicMock()
        mock_aimitsu.login.return_value = None
        mock_aimitsu_cls.return_value = mock_aimitsu

        result = runner.invoke(app, ["login"])

    assert result.exit_code == 0
    assert "OK" in result.output


def test_login_hnavi_failure(mock_playwright):
    """Test login failure for hnavi."""
    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_hnavi_cls,
        patch("tai.core.sales.AimitsuClient") as mock_aimitsu_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_hnavi = MagicMock()
        mock_hnavi.login.side_effect = RuntimeError("Login failed")
        mock_hnavi_cls.return_value = mock_hnavi

        mock_aimitsu = MagicMock()
        mock_aimitsu.login.return_value = None
        mock_aimitsu_cls.return_value = mock_aimitsu

        result = runner.invoke(app, ["login"])

    assert result.exit_code == 0  # Still exits 0 since it's a test command
    assert "Failed" in result.output


# ── status command tests ─────────────────────────────────────────────────────


def test_status_success(mock_playwright):
    """Test status shows summary."""
    from tai.core.sales.hnavi import HnaviJob, HnaviNegotiation
    from tai.core.sales.aimitsu import AimitsuProject

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_hnavi_cls,
        patch("tai.core.sales.AimitsuClient") as mock_aimitsu_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_hnavi = MagicMock()
        mock_hnavi.list_jobs.return_value = [HnaviJob(id="1", title="Job")]
        mock_hnavi.list_negotiations.return_value = [HnaviNegotiation(id="2", title="Neg")]
        mock_hnavi_cls.return_value = mock_hnavi

        mock_aimitsu = MagicMock()
        mock_aimitsu.list_projects.return_value = [AimitsuProject(no="3", title="Proj")]
        mock_aimitsu_cls.return_value = mock_aimitsu

        result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "Hnavi" in result.output
    assert "Aimitsu" in result.output


def test_status_json(mock_playwright):
    """Test status with --json."""
    from tai.core.sales.hnavi import HnaviJob, HnaviNegotiation
    from tai.core.sales.aimitsu import AimitsuProject

    with (
        patch("tai.core.sales.SalesBrowser") as mock_browser_cls,
        patch("tai.core.sales.HnaviClient") as mock_hnavi_cls,
        patch("tai.core.sales.AimitsuClient") as mock_aimitsu_cls,
    ):
        mock_browser = MagicMock()
        mock_browser.__enter__ = MagicMock(return_value=mock_browser)
        mock_browser.__exit__ = MagicMock(return_value=False)
        mock_browser_cls.return_value = mock_browser

        mock_hnavi = MagicMock()
        mock_hnavi.list_jobs.return_value = [HnaviJob(id="1", title="Job")]
        mock_hnavi.list_negotiations.return_value = []
        mock_hnavi_cls.return_value = mock_hnavi

        mock_aimitsu = MagicMock()
        mock_aimitsu.list_projects.return_value = []
        mock_aimitsu_cls.return_value = mock_aimitsu

        result = runner.invoke(app, ["status", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "hnavi" in data
    assert "aimitsu" in data
    assert data["hnavi"]["jobs"] == 1
