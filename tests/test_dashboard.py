"""Tests for `tai dashboard` — covers SPEC-dashboard-render R1–R8 + INV1, INV2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tai.main import app
from tai.commands import dashboard as dash

runner = CliRunner()


def _make_docs(root: Path) -> Path:
    docs = root / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "decisions").mkdir()
    (root / ".git").mkdir()
    (docs / "prd.md").write_text("---\nid: prd\ntype: prd\nparent: null\nchildren: []\nrelated: []\nstatus: draft\n---\n# PRD\n")
    (docs / "architecture.md").write_text(
        "---\nid: architecture\ntype: architecture\nparent: null\nchildren: [SPEC-x-y]\nrelated: [prd]\n---\n# Arch\n"
    )
    (docs / "specs" / "x-y.md").write_text(
        "---\nid: SPEC-x-y\ntype: spec\nstatus: approved\nparent: architecture\nchildren: []\nrelated: []\n---\n# X\n"
    )
    (docs / "specs" / "z-w.md").write_text(
        "---\nid: SPEC-z-w\ntype: spec\nstatus: draft\nparent: architecture\nchildren: []\nrelated: []\n---\n# Z\n"
    )
    (docs / "matrix.md").write_text(
        "---\nid: matrix\ntype: matrix\nparent: null\nchildren: []\nrelated: []\n---\n"
        "# Matrix\n## Coverage Summary\n- Total Behavior rows: 4\n- COVERED: 3\n"
    )
    (docs / "REVIEW.md").write_text(
        "---\nid: review\ntype: review\nparent: null\nchildren: []\nrelated: []\n---\n# Log\n"
        "## Open Items\n### [REVIEW-001] Approve the thing\n- **Status:** PENDING\n\n## Resolved Items\n"
    )
    (docs / "changelog.md").write_text(
        "---\nid: changelog\ntype: changelog\nparent: null\nchildren: []\nrelated: []\n---\n"
        "# Changelog\n## Unreleased\n- Added dashboard\n- Fixed a bug\n"
    )
    return docs


@pytest.fixture()
def docs_repo(tmp_path, monkeypatch):
    _make_docs(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


# covers: SPEC-dashboard-render R1
def test_R1_renders_sections(docs_repo):
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 0
    for section in ("Pipeline", "Needs you", "Recent", "Doc Health"):
        assert section in result.output


# covers: SPEC-dashboard-render R2
def test_R2_pipeline_counts_by_status(docs_repo):
    pipe = dash.collect_pipeline(docs_repo / "docs")
    assert pipe == {"draft": 1, "approved": 1, "implemented": 0, "total": 2}


# covers: SPEC-dashboard-render R3
def test_R3_needs_you_lists_pending(docs_repo):
    items = dash.collect_needs_you(docs_repo / "docs")
    assert len(items) == 1
    assert items[0]["id"] == "REVIEW-001"
    assert "Approve the thing" in items[0]["title"]


# covers: SPEC-dashboard-render R4
def test_R4_coverage_from_matrix(docs_repo):
    cov = dash.collect_coverage(docs_repo / "docs")
    assert cov == {"covered": 3, "total": 4, "percent": 75.0}


# covers: SPEC-dashboard-render R5
def test_R5_recent_from_changelog(docs_repo):
    recent = dash.collect_recent(docs_repo / "docs")
    assert recent[0]["version"] == "Unreleased"
    assert "Added dashboard" in recent[0]["entries"]


# covers: SPEC-dashboard-render R6
def test_R6_no_docs_exits_1_with_hint(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 1
    assert "No docs/" in result.output or "docs" in result.output.lower()


# covers: SPEC-dashboard-render R7
def test_R7_doc_health_flags_issues(docs_repo):
    docs = docs_repo / "docs"
    (docs / "specs" / "bad.md").write_text("no frontmatter here\n")
    (docs / "specs" / "orphan.md").write_text(
        "---\nid: SPEC-orphan\ntype: spec\nstatus: draft\nparent: null\nchildren: []\nrelated: []\n---\n"
    )
    (docs / "specs" / "brokenlink.md").write_text(
        "---\nid: SPEC-bl\ntype: spec\nstatus: draft\nparent: architecture\nchildren: []\nrelated: [does-not-exist]\n---\n"
    )
    h = dash.collect_doc_health(docs)
    assert any("bad.md" in m for m in h["missing_frontmatter"])
    assert any("orphan.md" in o for o in h["orphans"])
    assert any("does-not-exist" in b for b in h["broken_links"])
    # R7: warnings don't fail the command
    assert runner.invoke(app, ["dashboard"]).exit_code == 0


# covers: SPEC-dashboard-render R8
def test_R8_json_output(docs_repo):
    result = runner.invoke(app, ["dashboard", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert set(data) == {"pipeline", "coverage", "needs_you", "recent", "doc_health"}
    assert data["pipeline"]["total"] == 2
    assert data["coverage"]["percent"] == 75.0


# covers: SPEC-dashboard-render INV1 (read-only)
def test_INV1_read_only(docs_repo):
    docs = docs_repo / "docs"
    before = {p: p.read_bytes() for p in docs.rglob("*.md")}
    names_before = set(docs.rglob("*"))
    runner.invoke(app, ["dashboard"])
    runner.invoke(app, ["dashboard", "--json"])
    after = {p: p.read_bytes() for p in docs.rglob("*.md")}
    assert before == after, "dashboard must not modify any docs/ file"
    assert names_before == set(docs.rglob("*")), "dashboard must not add/remove files"


# covers: SPEC-dashboard-render INV2 (never crash on malformed doc)
def test_INV2_malformed_doc_does_not_crash(docs_repo):
    docs = docs_repo / "docs"
    (docs / "specs" / "junk.md").write_text("---\n:::: not yaml ::::\n[unclosed\n---\n")
    (docs / "matrix.md").write_text("---\nbroken\n# no coverage summary\n")
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 0
    assert dash.build_dashboard(docs) is not None
