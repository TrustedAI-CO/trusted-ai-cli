"""Tests for `tai dashboard list/search/show` — covers SPEC-docs-query R1-R8 + INV1, INV2."""

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
    (docs / "specs" / "auth-login.md").write_text(
        "---\nid: SPEC-auth-login\ntype: spec\nstatus: approved\nparent: architecture\nchildren: []\nrelated: []\n---\n# Auth Login — Spec\nbody about authentication\n"
    )
    (docs / "specs" / "notes-add.md").write_text(
        "---\nid: SPEC-notes-add\ntype: spec\nstatus: draft\nparent: architecture\nchildren: []\nrelated: []\n---\n# Notes Add — Spec\n"
    )
    (docs / "decisions" / "0001-stack.md").write_text(
        "---\nid: 0001-stack\ntype: decision\nstatus: proposed\nparent: architecture\nchildren: []\nrelated: []\n---\n# 0001-stack: Pick a stack\n"
    )
    (docs / "specs" / "spec.template.md").write_text("---\nid: SPEC-x\ntype: spec\n---\n# template\n")
    return docs


@pytest.fixture()
def docs_repo(tmp_path, monkeypatch):
    _make_docs(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


# covers: SPEC-docs-query R1
def test_R1_list_all(docs_repo):
    result = runner.invoke(app, ["dashboard", "list"])
    assert result.exit_code == 0
    assert "SPEC-auth-login" in result.output and "0001-stack" in result.output
    assert "SPEC-x" not in result.output  # template excluded


# covers: SPEC-docs-query R2
def test_R2_filter_type(docs_repo):
    rows = dash.collect_list(docs_repo / "docs", type_filter="spec")
    ids = {r.id for r in rows}
    assert ids == {"SPEC-auth-login", "SPEC-notes-add"}


# covers: SPEC-docs-query R3
def test_R3_filter_status(docs_repo):
    rows = dash.collect_list(docs_repo / "docs", status_filter="draft")
    assert [r.id for r in rows] == ["SPEC-notes-add"]


# covers: SPEC-docs-query R4
def test_R4_search(docs_repo):
    rows = dash.collect_search(docs_repo / "docs", "authentication")
    assert any(r.id == "SPEC-auth-login" for r in rows)
    # id hit ranks first
    rows2 = dash.collect_search(docs_repo / "docs", "auth")
    assert rows2[0].id == "SPEC-auth-login"


# covers: SPEC-docs-query R5
def test_R5_show(docs_repo):
    result = runner.invoke(app, ["dashboard", "show", "SPEC-auth-login"])
    assert result.exit_code == 0
    assert "Auth Login" in result.output and "authentication" in result.output


# covers: SPEC-docs-query R6
def test_R6_show_not_found(docs_repo):
    result = runner.invoke(app, ["dashboard", "show", "NOPE"])
    assert result.exit_code == 1
    # partial id surfaces the nearest-id hint
    hinted = runner.invoke(app, ["dashboard", "show", "auth"])
    assert hinted.exit_code == 1
    assert "SPEC-auth-login" in hinted.output  # "Did you mean" hint


# covers: SPEC-docs-query R7
def test_R7_json(docs_repo):
    result = runner.invoke(app, ["dashboard", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert {d["id"] for d in data} == {"SPEC-auth-login", "SPEC-notes-add", "0001-stack"}


# covers: SPEC-docs-query R8
def test_R8_no_docs(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["dashboard", "list"]).exit_code == 1


# covers: SPEC-docs-query INV1
def test_INV1_read_only(docs_repo):
    docs = docs_repo / "docs"
    before = {p: p.read_bytes() for p in docs.rglob("*.md")}
    runner.invoke(app, ["dashboard", "list"])
    runner.invoke(app, ["dashboard", "search", "auth"])
    runner.invoke(app, ["dashboard", "show", "SPEC-auth-login"])
    after = {p: p.read_bytes() for p in docs.rglob("*.md")}
    assert before == after


# covers: SPEC-docs-query INV2
def test_INV2_malformed(docs_repo):
    (docs_repo / "docs" / "specs" / "junk.md").write_text("---\n::: bad\n[unclosed\n")
    assert runner.invoke(app, ["dashboard", "list"]).exit_code == 0
    assert dash.collect_search(docs_repo / "docs", "x") is not None
