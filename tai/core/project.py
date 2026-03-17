"""Project manifest — reads/writes .tai.toml and locates the git repo root."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import tomli_w
from pydantic import BaseModel, field_validator

from tai.core.errors import ProjectError

_NOTION_ID_RE = re.compile(r"([0-9a-f]{32})", re.IGNORECASE)

MANIFEST_FILE = ".tai.toml"


class ProjectManifest(BaseModel):
    notion_page: str  # bare 32-char Notion page ID

    @field_validator("notion_page", mode="before")
    @classmethod
    def extract_notion_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("notion_page must not be empty")
        match = _NOTION_ID_RE.search(v)
        if not match:
            raise ValueError(
                f"Could not find a Notion page ID (32 hex chars) in: {v!r}"
            )
        return match.group(1)


def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk up from *start* (default: cwd) until a .git entry is found."""
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def load_manifest(root: Path) -> ProjectManifest | None:
    """Return the ProjectManifest from *root*/.tai.toml, or None if missing."""
    path = root / MANIFEST_FILE
    if not path.exists():
        return None

    with path.open("rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    notion_page = project.get("notion_page", "")
    if not notion_page:
        raise ProjectError(
            f"{MANIFEST_FILE} is missing a valid [project] notion_page",
        )

    return ProjectManifest(notion_page=notion_page)


def save_manifest(manifest: ProjectManifest, root: Path) -> None:
    """Write *manifest* to *root*/.tai.toml."""
    path = root / MANIFEST_FILE
    data = {"project": manifest.model_dump()}
    with path.open("wb") as f:
        tomli_w.dump(data, f)
