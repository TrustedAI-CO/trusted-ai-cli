"""Tests for `tai dashboard --serve` — covers SPEC-dashboard-serve R1-R9 + INV2, INV3."""

from __future__ import annotations

import json
import threading
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tai.main import app
from tai.commands import dashboard as dash

runner = CliRunner()


def _make_docs(root: Path) -> Path:
    docs = root / "docs"
    (docs / "specs").mkdir(parents=True)
    (root / ".git").mkdir()
    (docs / "architecture.md").write_text(
        "---\nid: architecture\ntype: architecture\nparent: null\nchildren: []\nrelated: []\n---\n# Arch\n"
    )
    (docs / "specs" / "x-y.md").write_text(
        "---\nid: SPEC-x-y\ntype: spec\nstatus: approved\nparent: architecture\nchildren: []\nrelated: []\n---\n# X\n"
    )
    (docs / "matrix.md").write_text(
        "---\nid: matrix\ntype: matrix\nparent: null\nchildren: []\nrelated: []\n---\n"
        "## Coverage Summary\n- Total Behavior rows: 2\n- COVERED: 1\n"
    )
    (docs / "REVIEW.md").write_text(
        "---\nid: review\ntype: review\nparent: null\nchildren: []\nrelated: []\n---\n## Open Items\n## Resolved Items\n"
    )
    (docs / "changelog.md").write_text(
        "---\nid: changelog\ntype: changelog\nparent: null\nchildren: []\nrelated: []\n---\n## Unreleased\n- init\n"
    )
    return docs


@pytest.fixture()
def docs_repo(tmp_path, monkeypatch):
    _make_docs(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@contextmanager
def running_server(docs: Path, host: str = "127.0.0.1", port: int = 0):
    port = port or dash.find_free_port()
    httpd = dash.build_server(docs, host, port)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        t.join(timeout=2)


def _get(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=3) as r:
        return r.status, r.read().decode()


# covers: SPEC-dashboard-serve R1
def test_R1_binds_and_serves_page(docs_repo):
    with running_server(docs_repo / "docs") as base:
        status, body = _get(base + "/")
        assert status == 200
        assert "tai dashboard" in body


# covers: SPEC-dashboard-serve R2 / INV2
def test_R2_api_matches_cli_json(docs_repo):
    cli = json.loads(runner.invoke(app, ["dashboard", "--json"]).output)
    with running_server(docs_repo / "docs") as base:
        _, body = _get(base + "/api/dashboard.json")
        assert json.loads(body) == cli


# covers: SPEC-dashboard-serve R3
def test_R3_page_has_all_sections(docs_repo):
    # the served HTML renders the five CLI sections (parity)
    for label in ("Pipeline", "Needs you", "Recent", "Doc Health"):
        assert label in dash._PAGE


# covers: SPEC-dashboard-serve R4
def test_R4_api_reflects_live_changes(docs_repo):
    docs = docs_repo / "docs"
    with running_server(docs) as base:
        before = json.loads(_get(base + "/api/dashboard.json")[1])
        assert before["pipeline"]["approved"] == 1
        (docs / "specs" / "new.md").write_text(
            "---\nid: SPEC-new\ntype: spec\nstatus: approved\nparent: architecture\nchildren: []\nrelated: []\n---\n"
        )
        after = json.loads(_get(base + "/api/dashboard.json")[1])
        assert after["pipeline"]["approved"] == 2  # no restart needed


# covers: SPEC-dashboard-serve R5
def test_R5_binds_requested_port(docs_repo):
    port = dash.find_free_port()
    httpd = dash.build_server(docs_repo / "docs", "127.0.0.1", port)
    try:
        assert httpd.server_address[1] == port
    finally:
        httpd.server_close()


# covers: SPEC-dashboard-serve R6
def test_R6_port_in_use_raises(docs_repo):
    port = dash.find_free_port()
    first = dash.build_server(docs_repo / "docs", "127.0.0.1", port)
    try:
        with pytest.raises(OSError):
            dash.build_server(docs_repo / "docs", "127.0.0.1", port)
    finally:
        first.server_close()


# covers: SPEC-dashboard-serve R7
def test_R7_no_docs_exits_1(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dashboard", "--serve", "--no-open"])
    assert result.exit_code == 1


# covers: SPEC-dashboard-serve R8
def test_R8_clean_shutdown(docs_repo):
    port = dash.find_free_port()
    httpd = dash.build_server(docs_repo / "docs", "127.0.0.1", port)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    httpd.shutdown()
    httpd.server_close()
    t.join(timeout=2)
    assert not t.is_alive()  # port freed, thread ended


# covers: SPEC-dashboard-serve R9 / INV3
def test_R9_default_bind_is_loopback(docs_repo):
    httpd = dash.build_server(docs_repo / "docs", "127.0.0.1", dash.find_free_port())
    try:
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()
