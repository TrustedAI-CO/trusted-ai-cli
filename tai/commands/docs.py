"""tai docs — documentation utilities for skills."""

from __future__ import annotations

import json
import re
from pathlib import Path

DOCS_DIR_NAME = "docs"
ASSETS_DIR = "_assets"

# Bundled assets shipped with tai
_BUNDLED_ASSETS = Path(__file__).resolve().parent.parent / "data" / "docs" / "assets"


# ── Validation schemas ──────────────────────────────────────────────────────

SCHEMAS: dict[str, dict] = {
    "intent": {
        "required_sections": ["context", "problem", "solution", "success-criteria"],
        "required_meta": ["date"],
    },
    "decision": {
        "required_sections": ["context", "decision", "consequences"],
        "required_meta": ["date", "status"],
    },
    "design": {
        "required_sections": ["overview", "components"],
        "required_meta": ["date"],
    },
    "spec": {
        "required_sections": ["problem", "requirements", "acceptance-criteria"],
        "required_meta": ["date", "status"],
    },
    "guide": {
        "required_sections": ["overview"],
        "required_meta": ["date"],
    },
    "plan": {
        "required_sections": ["phases"],
        "required_meta": ["date"],
    },
    "review": {
        "required_sections": ["findings"],
        "required_meta": ["date"],
    },
    "trace": {
        "required_sections": [],
        "required_meta": ["date"],
    },
    "changelog": {
        "required_sections": [],
        "required_meta": ["date"],
    },
}


def find_docs_root() -> Path:
    """Walk up from cwd to find the docs/ directory."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / DOCS_DIR_NAME
        if candidate.is_dir():
            return candidate
        if (parent / ".git").exists():
            return candidate
    return cwd / DOCS_DIR_NAME


def discover_docs(docs_root: Path) -> list[dict]:
    """Find all .html docs under docs_root, extract title and metadata."""
    docs = []
    if not docs_root.is_dir():
        return docs

    for html_file in sorted(docs_root.rglob("*.html")):
        rel = html_file.relative_to(docs_root)
        if rel.parts[0] == ASSETS_DIR:
            continue

        text = html_file.read_text(encoding="utf-8", errors="replace")
        title = _extract_title(text) or rel.stem
        doc_type = _extract_meta(text, "doc-type") or ""

        docs.append({
            "path": str(rel),
            "title": title,
            "type": doc_type,
        })
    return docs


def validate_file(path: Path, docs_root: Path) -> list[str]:
    """Validate a single HTML doc. Returns list of issues."""
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []

    title = _extract_title(text)
    doc_type = _extract_meta(text, "doc-type")
    doc_date = _extract_meta(text, "doc-date")

    if not title or title == "Untitled":
        issues.append("Missing <title>")
    if not doc_type:
        issues.append('Missing <meta name="doc-type">')
    if not doc_date:
        issues.append('Missing <meta name="doc-date">')

    schema = SCHEMAS.get(doc_type or "")
    if schema:
        for section in schema["required_sections"]:
            if f'data-section="{section}"' not in text:
                issues.append(f"Missing section: {section}")
        for meta_field in schema["required_meta"]:
            if not _extract_meta(text, f"doc-{meta_field}"):
                issues.append(f"Missing meta: doc-{meta_field}")
    elif doc_type:
        issues.append(f"Unknown doc-type: {doc_type}")

    for href in _extract_internal_links(text):
        target = (path.parent / href).resolve()
        if not target.exists():
            issues.append(f"Broken link: {href}")

    return issues


def validate_all(docs_root: Path) -> dict[str, list[str]]:
    """Validate every HTML doc under docs_root. Returns {path: [issues]}."""
    results: dict[str, list[str]] = {}
    if not docs_root.is_dir():
        return results

    for html_file in sorted(docs_root.rglob("*.html")):
        rel = html_file.relative_to(docs_root)
        if rel.parts[0] == ASSETS_DIR:
            continue
        file_issues = validate_file(html_file, docs_root)
        if file_issues:
            results[str(rel)] = file_issues
    return results


# ── HTML parsing helpers (no external deps) ─────────────────────────────────

_RE_TITLE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)
_RE_META = re.compile(r'<meta\s+name="([^"]+)"\s+content="([^"]*)"', re.IGNORECASE)
_RE_HREF = re.compile(r'<a\s[^>]*href="([^"#][^"]*)"', re.IGNORECASE)


def _extract_title(html: str) -> str | None:
    m = _RE_TITLE.search(html)
    return m.group(1).strip() if m else None


def _extract_meta(html: str, name: str) -> str | None:
    for m in _RE_META.finditer(html):
        if m.group(1) == name:
            return m.group(2)
    return None


def _extract_internal_links(html: str) -> list[str]:
    links = []
    for m in _RE_HREF.finditer(html):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:", "/")):
            continue
        links.append(href)
    return links


# ── Asset management ────────────────────────────────────────────────────────

def _copy_assets(target: Path) -> None:
    """Copy bundled CSS/JS assets to the project's docs/_assets/."""
    import shutil
    if target.is_dir():
        shutil.rmtree(target)
    shutil.copytree(_BUNDLED_ASSETS, target)


def write_index(docs_root: Path) -> None:
    """Inject a static <nav> sidebar into every HTML file. No JS needed."""
    docs = discover_docs(docs_root)

    # Group by directory
    groups: dict[str, list[dict]] = {}
    for doc in docs:
        parts = doc["path"].split("/")
        d = parts[0] if len(parts) > 1 else ""
        groups.setdefault(d, []).append(doc)

    for html_file in sorted(docs_root.rglob("*.html")):
        rel = html_file.relative_to(docs_root)
        if rel.parts[0] == ASSETS_DIR:
            continue

        current = str(rel)
        depth = len(rel.parts) - 1
        prefix = "../" * depth

        # Build nav HTML
        lines = ['<nav class="docs-nav">']
        lines.append(f'  <a class="nav-title" href="{prefix}index.html">Docs</a>')

        for d in sorted(groups, key=lambda x: (x != "", x)):
            if d:
                lines.append(f'  <div class="nav-group">{d}</div>')
                lines.append('  <div class="nav-group-items">')

            for doc in sorted(groups[d], key=lambda x: x["title"]):
                href = prefix + doc["path"]
                active = " active" if doc["path"] == current else ""
                lines.append(
                    f'    <a class="nav-link{active}" href="{href}">{doc["title"]}</a>'
                )

            if d:
                lines.append('  </div>')

        lines.append('</nav>')
        nav_html = "\n".join(lines)

        text = html_file.read_text(encoding="utf-8")

        # Remove old nav if present
        text = re.sub(
            r'<nav class="docs-nav">.*?</nav>\s*',
            '',
            text,
            flags=re.DOTALL,
        )

        # Normalize body tag and insert nav
        text = re.sub(r'<body[^>]*>', '<body class="has-nav">', text, count=1)
        text = text.replace('<body class="has-nav">', f'<body class="has-nav">\n{nav_html}', 1)

        html_file.write_text(text, encoding="utf-8")
