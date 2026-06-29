"""Tests for `tai dashboard gates` — covers SPEC-gates-view R1-R8 + INV1, INV2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tai.main import app
from tai.commands import dashboard as dash

runner = CliRunner()


def _make_docs(root: Path, *, prd_status="draft", with_pending=True) -> Path:
    docs = root / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "decisions").mkdir()
    (root / ".git").mkdir()
    (docs / "prd.md").write_text(
        f"---\nid: prd\ntype: prd\nparent: null\nchildren: []\nrelated: []\nstatus: {prd_status}\n---\n# Product\n"
    )
    (docs / "specs" / "draft-spec.md").write_text(
        "---\nid: SPEC-draft-one\ntype: spec\nstatus: draft\nparent: architecture\nchildren: []\nrelated: []\n---\n# Draft One\n"
    )
    (docs / "specs" / "done-spec.md").write_text(
        "---\nid: SPEC-done\ntype: spec\nstatus: implemented\nparent: architecture\nchildren: []\nrelated: []\n---\n# Done\n"
    )
    (docs / "decisions" / "0009-prop.md").write_text(
        "---\nid: 0009-prop\ntype: decision\nstatus: proposed\nparent: architecture\nchildren: []\nrelated: []\n---\n# 0009-prop: A choice\n"
    )
    review_items = (
        "## Open Items\n### [REVIEW-001] Decide retention\n- **Status:** PENDING\n\n## Resolved Items\n"
        if with_pending else "## Open Items\n\n## Resolved Items\n"
    )
    (docs / "REVIEW.md").write_text(
        f"---\nid: review\ntype: review\nparent: null\nchildren: []\nrelated: []\n---\n# Log\n{review_items}"
    )
    return docs


@pytest.fixture()
def docs_repo(tmp_path, monkeypatch):
    _make_docs(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


# covers: SPEC-gates-view R1
def test_R1_board_sections(docs_repo):
    result = runner.invoke(app, ["dashboard", "gates"])
    assert result.exit_code == 0
    for s in ("GATE A", "GATE B", "GATE C", "REVIEW"):
        assert s in result.output


# covers: SPEC-gates-view R2
def test_R2_draft_spec_to_gate_c(docs_repo):
    g = dash.collect_gates(docs_repo / "docs")
    assert any(i["id"] == "SPEC-draft-one" and i["action"] == "approve" for i in g["gate_c"])
    assert not any(i["id"] == "SPEC-done" for i in g["gate_c"])  # implemented not pending


# covers: SPEC-gates-view R3
def test_R3_proposed_adr_to_gate_b(docs_repo):
    g = dash.collect_gates(docs_repo / "docs")
    assert any(i["id"] == "0009-prop" and i["action"] == "accept" for i in g["gate_b"])


# covers: SPEC-gates-view R4
def test_R4_unsigned_prd_to_gate_a(docs_repo):
    g = dash.collect_gates(docs_repo / "docs")
    assert any(i["id"] == "prd" and i["action"] == "sign" for i in g["gate_a"])


# covers: SPEC-gates-view R5
def test_R5_review_pending_to_resolve(docs_repo):
    g = dash.collect_gates(docs_repo / "docs")
    assert g["review"] and g["review"][0]["action"] == "resolve"


# covers: SPEC-gates-view R6
def test_R6_all_clear(tmp_path, monkeypatch):
    _make_docs(tmp_path, prd_status="approved", with_pending=False)
    # remove the draft spec + proposed ADR so nothing is pending
    (tmp_path / "docs" / "specs" / "draft-spec.md").unlink()
    (tmp_path / "docs" / "decisions" / "0009-prop.md").unlink()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dashboard", "gates"])
    assert result.exit_code == 0
    assert "all clear" in result.output


# covers: SPEC-gates-view R7
def test_R7_json(docs_repo):
    result = runner.invoke(app, ["dashboard", "gates", "--json"])
    assert result.exit_code == 0
    g = json.loads(result.output)
    assert set(g) == {"gate_a", "gate_b", "gate_c", "review"}


# covers: SPEC-gates-view R8
def test_R8_no_docs(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["dashboard", "gates"]).exit_code == 1


# covers: SPEC-gates-view INV1
def test_INV1_read_only(docs_repo):
    docs = docs_repo / "docs"
    before = {p: p.read_bytes() for p in docs.rglob("*.md")}
    runner.invoke(app, ["dashboard", "gates"])
    after = {p: p.read_bytes() for p in docs.rglob("*.md")}
    assert before == after


# covers: SPEC-gates-view INV2
def test_INV2_malformed(docs_repo):
    (docs_repo / "docs" / "specs" / "junk.md").write_text("---\n:: broken\n")
    assert runner.invoke(app, ["dashboard", "gates"]).exit_code == 0


# covers: SPEC-gates-view INV2 — truncated REVIEW.md must not crash
def test_INV2_truncated_review(docs_repo):
    # REVIEW.md ending with a bare "### " (no following line) must not IndexError
    (docs_repo / "docs" / "REVIEW.md").write_text(
        "---\nid: review\ntype: review\nparent: null\nchildren: []\nrelated: []\n---\n## Open Items\n### "
    )
    assert runner.invoke(app, ["dashboard", "gates"]).exit_code == 0
    assert dash.collect_needs_you(docs_repo / "docs") is not None
