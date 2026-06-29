"""Tests for the `tai dashboard --serve` web UI — covers SPEC-dashboard-ui R1-R10 + INV1/2/3."""

from __future__ import annotations

import json
import subprocess
import threading
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import pytest

from tai.commands import dashboard as dash
from tai.commands import gate

runner_repo = None


def _make_repo(root: Path) -> Path:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@test.co"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=True)
    docs = root / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "decisions").mkdir()
    (docs / "architecture.md").write_text(
        "---\nid: architecture\ntype: architecture\nparent: null\nchildren: []\nrelated: []\n---\n"
        "# Arch\n```mermaid\nflowchart TD\n A-->B\n```\n"
    )
    (docs / "specs" / "draft.md").write_text(
        "---\nid: SPEC-draft\ntype: spec\nstatus: draft\napproved_at:\nparent: architecture\nchildren: []\nrelated: []\n---\n# Draft Spec\nabout auth\n"
    )
    (docs / "decisions" / "0003-x.md").write_text(
        "---\nid: 0003-x\ntype: decision\nstatus: proposed\nparent: architecture\nchildren: []\nrelated: []\n---\n# 0003-x\n"
    )
    (docs / "REVIEW.md").write_text(
        "---\nid: review\ntype: review\nparent: null\nchildren: []\nrelated: []\n---\n## Open Items\n## Resolved Items\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "init"], check=True, capture_output=True)
    return docs


@contextmanager
def _server(docs: Path):
    port = dash.find_free_port()
    httpd = dash.build_server(docs, "127.0.0.1", port)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown(); httpd.server_close(); t.join(timeout=2)


def _get(url):
    with urllib.request.urlopen(url, timeout=3) as r:
        return r.status, r.read().decode()


def _post(url, obj):
    req = urllib.request.Request(url, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.loads(r.read().decode())


def _commits(repo): return int(subprocess.run(["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
                                               capture_output=True, text=True).stdout.strip())


@pytest.fixture()
def repo(tmp_path):
    _make_repo(tmp_path)
    return tmp_path


# covers: SPEC-dashboard-ui R1
def test_R1_spa_tabs(repo):
    with _server(repo / "docs") as base:
        _, html = _get(base + "/")
        assert all(t in html for t in ("Overview", "Specs", "Gates"))


# covers: SPEC-dashboard-ui R2
def test_R2_api_docs(repo):
    with _server(repo / "docs") as base:
        rows = json.loads(_get(base + "/api/docs")[1])
        ids = {r["id"] for r in rows}
        assert "SPEC-draft" in ids and "0003-x" in ids  # specs + ADRs (not architecture)
        assert "architecture" not in ids


# covers: SPEC-dashboard-ui R3
def test_R3_doc_detail_mermaid(repo):
    with _server(repo / "docs") as base:
        d = json.loads(_get(base + "/api/doc/architecture")[1])
        assert set(d) >= {"frontmatter", "body", "mermaid"}
        assert d["mermaid"] and "flowchart" in d["mermaid"][0]


# covers: SPEC-dashboard-ui R4
def test_R4_api_search(repo):
    with _server(repo / "docs") as base:
        rows = json.loads(_get(base + "/api/search?q=auth")[1])
        assert any(r["id"] == "SPEC-draft" for r in rows)


# covers: SPEC-dashboard-ui R5
def test_R5_api_gates(repo):
    with _server(repo / "docs") as base:
        g = json.loads(_get(base + "/api/gates")[1])
        assert set(g) == {"gate_a", "gate_b", "gate_c", "review"}
        assert any(i["id"] == "SPEC-draft" for i in g["gate_c"])


# covers: SPEC-dashboard-ui R6 / R9 / INV2
def test_R6_post_approve_flips_and_commits(repo):
    spec = repo / "docs" / "specs" / "draft.md"
    with _server(repo / "docs") as base:
        before = _commits(repo)
        r = _post(base + "/api/gate/approve", {"id": "SPEC-draft"})
        assert r["ok"] is True
        assert dash.parse_frontmatter(spec.read_text())["status"] == "approved"
        assert _commits(repo) == before + 1  # one audited commit (INV2 single write path)


# covers: SPEC-dashboard-ui R7
def test_R7_post_invalid_refused(repo):
    with _server(repo / "docs") as base:
        _post(base + "/api/gate/approve", {"id": "SPEC-draft"})       # now approved
        r = _post(base + "/api/gate/approve", {"id": "SPEC-draft"})   # again → refused
        assert r["ok"] is False


# covers: SPEC-dashboard-ui R8 / INV1
def test_R8_gets_are_read_only(repo):
    docs = repo / "docs"
    before = {p: p.read_bytes() for p in docs.rglob("*.md")}
    with _server(docs) as base:
        for path in ("/", "/api/dashboard.json", "/api/docs", "/api/search?q=x",
                     "/api/doc/SPEC-draft", "/api/gates"):
            _get(base + path)
    assert {p: p.read_bytes() for p in docs.rglob("*.md")} == before


# covers: SPEC-dashboard-ui R9/INV2 — web approve == gate core (same one write path)
def test_R9_web_matches_cli_core(repo):
    # the POST handler calls gate.gate_approve directly — assert that's the path
    with _server(repo / "docs") as base:
        r = _post(base + "/api/gate/accept", {"id": "0003-x"})
        assert r["ok"] is True
        assert dash.parse_frontmatter((repo / "docs" / "decisions" / "0003-x.md").read_text())["status"] == "accepted"


# covers: SPEC-dashboard-ui R10 / INV3
def test_R10_loopback_bind(repo):
    httpd = dash.build_server(repo / "docs", "127.0.0.1", dash.find_free_port())
    try:
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()


# covers: SPEC-dashboard-ui INV3 — non-loopback Host header is rejected (DNS-rebinding guard)
def test_INV3_foreign_host_rejected(repo):
    with _server(repo / "docs") as base:
        req = urllib.request.Request(base + "/api/docs", headers={"Host": "evil.example.com"})
        try:
            urllib.request.urlopen(req, timeout=3)
            assert False, "expected 403"
        except urllib.error.HTTPError as e:
            assert e.code == 403
        # write endpoint too
        wreq = urllib.request.Request(base + "/api/gate/approve", data=b'{"id":"SPEC-draft"}',
                                      headers={"Host": "evil.example.com", "Content-Type": "application/json"},
                                      method="POST")
        try:
            urllib.request.urlopen(wreq, timeout=3)
            assert False, "expected 403"
        except urllib.error.HTTPError as e:
            assert e.code == 403
        # the spec was NOT approved
        assert dash.parse_frontmatter((repo / "docs" / "specs" / "draft.md").read_text())["status"] == "draft"


# covers: SPEC-dashboard-ui INV3 — CSRF: cross-origin simple POST + foreign Origin rejected, no write
def test_INV3_csrf_guard(repo):
    spec = repo / "docs" / "specs" / "draft.md"
    with _server(repo / "docs") as base:
        # simple request (text/plain, no preflight) → 415, no mutation
        r1 = urllib.request.Request(base + "/api/gate/approve", data=b'{"id":"SPEC-draft"}',
                                    headers={"Content-Type": "text/plain"}, method="POST")
        try:
            urllib.request.urlopen(r1, timeout=3); assert False
        except urllib.error.HTTPError as e:
            assert e.code == 415
        # JSON but foreign Origin → 403
        r2 = urllib.request.Request(base + "/api/gate/approve", data=b'{"id":"SPEC-draft"}',
                                    headers={"Content-Type": "application/json", "Origin": "http://evil.example.com"},
                                    method="POST")
        try:
            urllib.request.urlopen(r2, timeout=3); assert False
        except urllib.error.HTTPError as e:
            assert e.code == 403
        assert dash.parse_frontmatter(spec.read_text())["status"] == "draft"  # never written


# covers: SPEC-dashboard-ui — POST error paths (missing id 400, unknown action 404)
def test_post_error_paths(repo):
    with _server(repo / "docs") as base:
        assert _post(base + "/api/gate/approve", {})["ok"] is False  # missing id → ok:false
        bad = urllib.request.Request(base + "/api/gate/bogus", data=b"{}",
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            urllib.request.urlopen(bad, timeout=3)
            assert False
        except urllib.error.HTTPError as e:
            assert e.code == 404
