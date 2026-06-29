"""Tests for `tai gate` — covers SPEC-gates-action R1-R10 + INV2, INV4."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tai.main import app
from tai.commands.dashboard import parse_frontmatter

runner = CliRunner()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _make_repo(root: Path) -> Path:
    _git(root.parent if False else root, "init") if False else None
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    _git(root, "config", "user.email", "t@test.co")
    _git(root, "config", "user.name", "Test")
    docs = root / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "decisions").mkdir()
    (docs / "specs" / "x-y.md").write_text(
        "---\nid: SPEC-x-y\ntype: spec\nstatus: draft\napproved_at:\nparent: architecture\nchildren: []\nrelated: []\n---\n# X\nbody line\n"
    )
    (docs / "specs" / "done.md").write_text(
        "---\nid: SPEC-done\ntype: spec\nstatus: implemented\nparent: architecture\nchildren: []\nrelated: []\n---\n# Done\n"
    )
    (docs / "decisions" / "0003-x.md").write_text(
        "---\nid: 0003-x\ntype: decision\nstatus: proposed\nparent: architecture\nchildren: []\nrelated: []\n---\n# 0003-x: choice\n"
    )
    (docs / "REVIEW.md").write_text(
        "---\nid: review\ntype: review\nparent: null\nchildren: []\nrelated: []\n---\n# Log\n"
        "## Open Items\n### [REVIEW-001] Decide retention\n- **Status:** PENDING\n\n## Resolved Items\n"
    )
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "init"], check=True, capture_output=True)
    return docs


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    _make_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _status(path: Path) -> str:
    return parse_frontmatter(path.read_text()).get("status")


def _commits(repo: Path) -> int:
    return int(_git(repo, "rev-list", "--count", "HEAD"))


# covers: SPEC-gates-action R1
def test_R1_approve_draft(repo):
    spec = repo / "docs" / "specs" / "x-y.md"
    r = runner.invoke(app, ["gate", "approve", "SPEC-x-y", "--yes"])
    assert r.exit_code == 0
    fm = parse_frontmatter(spec.read_text())
    assert fm["status"] == "approved" and fm["approved_at"]


# covers: SPEC-gates-action R2
def test_R2_approve_non_draft_refused(repo):
    spec = repo / "docs" / "specs" / "done.md"
    before = spec.read_text()
    r = runner.invoke(app, ["gate", "approve", "SPEC-done", "--yes"])
    assert r.exit_code == 1 and spec.read_text() == before


# covers: SPEC-gates-action R3
def test_R3_accept_proposed(repo):
    r = runner.invoke(app, ["gate", "accept", "0003-x", "--yes"])
    assert r.exit_code == 0
    assert _status(repo / "docs" / "decisions" / "0003-x.md") == "accepted"


# covers: SPEC-gates-action R4
def test_R4_accept_non_proposed_refused(repo):
    # accept a spec-as-adr mismatch: the ADR is now... use the draft spec id which isn't proposed
    r = runner.invoke(app, ["gate", "accept", "SPEC-x-y", "--yes"])
    assert r.exit_code == 1
    assert _status(repo / "docs" / "specs" / "x-y.md") == "draft"


# covers: SPEC-gates-action R5
def test_R5_resolve_pending(repo):
    r = runner.invoke(app, ["gate", "resolve", "REVIEW-001", "--yes"])
    assert r.exit_code == 0
    assert "RESOLVED" in (repo / "docs" / "REVIEW.md").read_text()


# covers: SPEC-gates-action R6
def test_R6_resolve_absent_refused(repo):
    before = (repo / "docs" / "REVIEW.md").read_text()
    r = runner.invoke(app, ["gate", "resolve", "REVIEW-999", "--yes"])
    assert r.exit_code == 1 and (repo / "docs" / "REVIEW.md").read_text() == before


# covers: SPEC-gates-action R7
def test_R7_unknown_id(repo):
    r = runner.invoke(app, ["gate", "approve", "NOPE", "--yes"])
    assert r.exit_code == 1


# covers: SPEC-gates-action R8
def test_R8_confirm_decline_no_write(repo):
    spec = repo / "docs" / "specs" / "x-y.md"
    before = spec.read_text()
    r = runner.invoke(app, ["gate", "approve", "SPEC-x-y"], input="n\n")
    assert r.exit_code == 1 and spec.read_text() == before


# covers: SPEC-gates-action R9 / INV2
def test_R9_body_unchanged(repo):
    spec = repo / "docs" / "specs" / "x-y.md"
    runner.invoke(app, ["gate", "approve", "SPEC-x-y", "--yes"])
    body = spec.read_text().split("---", 2)[2]
    assert body == "\n# X\nbody line\n"  # body byte-identical; only frontmatter changed


# covers: SPEC-gates-action R10 / INV4
def test_R10_one_audited_commit(repo):
    before = _commits(repo)
    runner.invoke(app, ["gate", "approve", "SPEC-x-y", "--yes"])
    assert _commits(repo) == before + 1
    msg = _git(repo, "log", "-1", "--format=%s")
    assert "SPEC-x-y" in msg and "approved" in msg
