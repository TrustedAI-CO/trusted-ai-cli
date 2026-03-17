"""Tests for tai/core/project.py — manifest read/write and repo root detection."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from tai.core.project import (
    ProjectManifest,
    find_repo_root,
    load_manifest,
    save_manifest,
)
from tai.core.errors import ProjectError


# ── find_repo_root ────────────────────────────────────────────────────────────


def test_find_repo_root_from_repo_root(tmp_path):
    (tmp_path / ".git").mkdir()
    assert find_repo_root(tmp_path) == tmp_path


def test_find_repo_root_from_subdir(tmp_path):
    (tmp_path / ".git").mkdir()
    subdir = tmp_path / "a" / "b" / "c"
    subdir.mkdir(parents=True)
    assert find_repo_root(subdir) == tmp_path


def test_find_repo_root_returns_none_outside_repo(tmp_path):
    # tmp_path has no .git anywhere up to filesystem root
    assert find_repo_root(tmp_path) is None


def test_find_repo_root_stops_at_git_file(tmp_path):
    """A .git *file* (worktree) should also count as a repo root."""
    (tmp_path / ".git").write_text("gitdir: ../.git/worktrees/foo")
    assert find_repo_root(tmp_path) == tmp_path


# ── load_manifest ─────────────────────────────────────────────────────────────


def test_load_manifest_reads_notion_page(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    manifest = load_manifest(tmp_path)
    assert manifest.notion_page == "2ef55eff03158039b95cf6e8ff60d632"


def test_load_manifest_returns_none_when_no_file(tmp_path):
    assert load_manifest(tmp_path) is None


def test_load_manifest_raises_on_missing_notion_page(tmp_path):
    (tmp_path / ".tai.toml").write_text("[project]\n")
    with pytest.raises(ProjectError, match="notion_page"):
        load_manifest(tmp_path)


def test_load_manifest_raises_on_empty_notion_page(tmp_path):
    (tmp_path / ".tai.toml").write_text('[project]\nnotion_page = ""\n')
    with pytest.raises(ProjectError, match="notion_page"):
        load_manifest(tmp_path)


# ── save_manifest ─────────────────────────────────────────────────────────────


def test_save_manifest_writes_toml(tmp_path):
    manifest = ProjectManifest(notion_page="2ef55eff03158039b95cf6e8ff60d632")
    save_manifest(manifest, tmp_path)

    with (tmp_path / ".tai.toml").open("rb") as f:
        data = tomllib.load(f)

    assert data["project"]["notion_page"] == "2ef55eff03158039b95cf6e8ff60d632"


def test_save_manifest_overwrites_existing(tmp_path):
    (tmp_path / ".tai.toml").write_text(
        '[project]\nnotion_page = "2ef55eff03158039b95cf6e8ff60d632"\n'
    )
    new_id = "abcdef1234567890abcdef1234567890"
    manifest = ProjectManifest(notion_page=new_id)
    save_manifest(manifest, tmp_path)

    with (tmp_path / ".tai.toml").open("rb") as f:
        data = tomllib.load(f)

    assert data["project"]["notion_page"] == new_id


def test_save_then_load_roundtrip(tmp_path):
    manifest = ProjectManifest(notion_page="2ef55eff03158039b95cf6e8ff60d632")
    save_manifest(manifest, tmp_path)
    loaded = load_manifest(tmp_path)
    assert loaded == manifest


# ── ProjectManifest validation ────────────────────────────────────────────────


def test_manifest_strips_notion_url_to_id():
    """Passing a full Notion URL should extract just the page ID."""
    m = ProjectManifest(
        notion_page="https://www.notion.so/Video-Research-2ef55eff03158039b95cf6e8ff60d632"
    )
    assert m.notion_page == "2ef55eff03158039b95cf6e8ff60d632"


def test_manifest_accepts_bare_id():
    m = ProjectManifest(notion_page="2ef55eff03158039b95cf6e8ff60d632")
    assert m.notion_page == "2ef55eff03158039b95cf6e8ff60d632"


def test_manifest_rejects_empty_id():
    with pytest.raises(Exception):
        ProjectManifest(notion_page="")
