"""tai dashboard — one-screen project overview from the docs/ document-driven tree.

Implements SPEC-dashboard-render. Read-only: never writes under docs/ (INV1) and never
raises on a malformed doc — issues degrade to Doc Health warnings (INV2).
"""

from __future__ import annotations

import json as _json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tai.core.context import get_ctx

app = typer.Typer(name="dashboard", help="One-screen project overview from docs/.")
console = Console()
err_console = Console(stderr=True)

_TEMPLATE = "template"
_LINK_FIELDS = ("parent", "children", "related")


# ── docs/ discovery ───────────────────────────────────────────────────────────

def find_docs_dir(start: Optional[Path] = None) -> Optional[Path]:
    """Locate the repo's docs/ dir by walking up from start (cwd). None if absent."""
    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        candidate = d / "docs"
        if candidate.is_dir():
            return candidate
        if (d / ".git").exists():
            break
    return None


# ── tolerant frontmatter parsing (no YAML dependency; never raises) ─────────────

def parse_frontmatter(text: str) -> dict:
    """Parse leading `---` frontmatter into a dict. Returns {} when absent/malformed.

    Handles `key: scalar`, `key: [a, b]`, and empty `key:`. Tolerant by design (INV2).
    """
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            out[key] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
        elif raw == "":
            out[key] = None
        else:
            out[key] = raw
    return out


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# ── data model ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Dashboard:
    pipeline: dict
    coverage: dict
    needs_you: list
    recent: list
    doc_health: dict

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "coverage": self.coverage,
            "needs_you": self.needs_you,
            "recent": self.recent,
            "doc_health": self.doc_health,
        }


# ── collectors (pure, read-only) ──────────────────────────────────────────────

def _md_docs(docs: Path) -> list:
    return [p for p in docs.rglob("*.md") if _TEMPLATE not in p.name.lower()]


def collect_pipeline(docs: Path) -> dict:
    """Spec counts grouped by status (R2)."""
    counts = {"draft": 0, "approved": 0, "implemented": 0}
    specs_dir = docs / "specs"
    if specs_dir.is_dir():
        for p in specs_dir.glob("*.md"):
            if _TEMPLATE in p.name.lower():
                continue
            status = parse_frontmatter(_read(p)).get("status")
            if status in counts:
                counts[status] += 1
    counts["total"] = sum(counts.values())
    return counts


def collect_coverage(docs: Path) -> dict:
    """COVERED / total from matrix.md Coverage Summary (R4)."""
    text = _read(docs / "matrix.md")
    total = _find_int(text, r"Total Behavior rows:\s*(\d+)")
    covered = _find_int(text, r"COVERED:\s*(\d+)")
    percent = round(100.0 * covered / total, 1) if total else None
    return {"covered": covered or 0, "total": total or 0, "percent": percent}


def _find_int(text: str, pattern: str) -> Optional[int]:
    m = re.search(pattern, text)
    return int(m.group(1)) if m else None


def collect_needs_you(docs: Path) -> list:
    """Open PENDING items from REVIEW.md (R3)."""
    text = _read(docs / "REVIEW.md")
    open_section = text.split("## Resolved", 1)[0]
    items = []
    # blocks start at "### [REVIEW-NNN] title"
    blocks = re.split(r"(?m)^### ", open_section)
    for block in blocks[1:]:
        header = block.splitlines()[0].strip()
        m = re.match(r"\[?(REVIEW-[\w-]+|[\w-]+)\]?\s*(.*)", header)
        rid = m.group(1) if m else "?"
        title = (m.group(2).strip() if m else header) or header
        if re.search(r"(?i)status:\**\s*pending", block):
            items.append({"id": rid, "title": title})
    return items


def collect_recent(docs: Path) -> list:
    """Newest changelog block's entries (R5)."""
    text = _read(docs / "changelog.md")
    out = []
    blocks = re.split(r"(?m)^## ", text)
    for block in blocks[1:]:
        lines = block.splitlines()
        version = lines[0].strip()
        entries = [l.strip()[2:].strip() for l in lines[1:] if l.strip().startswith("- ")]
        if entries:
            out.append({"version": version, "entries": entries})
    return out[:2]


def collect_doc_health(docs: Path) -> dict:
    """Missing frontmatter, orphans, broken links across the graph (R7)."""
    missing, broken = [], []
    ids: dict = {}
    parsed: dict = {}
    for p in _md_docs(docs):
        fm = parse_frontmatter(_read(p))
        rel = str(p.relative_to(docs))
        if not fm or "id" not in fm:
            missing.append(rel)
            continue
        parsed[p] = fm
        ids[fm["id"]] = rel

    referenced: set = set()
    for p, fm in parsed.items():
        rel = str(p.relative_to(docs))
        for fld in _LINK_FIELDS:
            val = fm.get(fld)
            targets = val if isinstance(val, list) else ([val] if val else [])
            for t in targets:
                if t in (None, "null"):
                    continue
                if t not in ids:
                    broken.append(f"{rel}: {fld} → '{t}' (no such doc)")
                else:
                    referenced.add(t)

    # Standalone root docs are flat by design (no parent, nothing links in). Only the
    # graph-participating source docs (spec, decision) are expected to be reachable.
    _flat_types = {"review", "prd", "matrix", "changelog", "contributing", "plan", "design", "architecture"}
    orphans = []
    for p, fm in parsed.items():
        doc_id, typ = fm.get("id"), fm.get("type")
        if typ in _flat_types:
            continue
        if fm.get("parent") in (None, "null") and doc_id not in referenced:
            orphans.append(str(p.relative_to(docs)))
    return {"orphans": orphans, "broken_links": broken, "missing_frontmatter": missing}


def build_dashboard(docs: Path) -> Dashboard:
    return Dashboard(
        pipeline=collect_pipeline(docs),
        coverage=collect_coverage(docs),
        needs_you=collect_needs_you(docs),
        recent=collect_recent(docs),
        doc_health=collect_doc_health(docs),
    )


# ── render ────────────────────────────────────────────────────────────────────

def render(d: Dashboard, out: Console) -> None:
    pipe = d.pipeline
    p = Table.grid(padding=(0, 2))
    p.add_row("Specs", f"{pipe['total']} total")
    p.add_row("  draft", str(pipe["draft"]))
    p.add_row("  approved", str(pipe["approved"]))
    p.add_row("  implemented", str(pipe["implemented"]))
    cov = d.coverage
    cov_str = f"{cov['covered']}/{cov['total']}" + (f" ({cov['percent']}%)" if cov["percent"] is not None else " (n/a)")
    p.add_row("Coverage", cov_str)
    out.print(Panel(p, title="Pipeline", border_style="cyan"))

    if d.needs_you:
        t = Table.grid(padding=(0, 2))
        for item in d.needs_you:
            t.add_row(f"[yellow]{item['id']}[/yellow]", item["title"])
        out.print(Panel(t, title=f"Needs you ({len(d.needs_you)})", border_style="yellow"))
    else:
        out.print(Panel("[green]nothing pending[/green]", title="Needs you (0)", border_style="green"))

    if d.recent:
        t = Table.grid(padding=(0, 2))
        for blk in d.recent:
            t.add_row(f"[bold]{blk['version']}[/bold]")
            for e in blk["entries"][:5]:
                t.add_row(f"  • {e}")
        out.print(Panel(t, title="Recent", border_style="blue"))

    h = d.doc_health
    issues = len(h["orphans"]) + len(h["broken_links"]) + len(h["missing_frontmatter"])
    if issues == 0:
        out.print(Panel("[green]healthy — graph intact[/green]", title="Doc Health", border_style="green"))
    else:
        t = Table.grid(padding=(0, 2))
        for o in h["missing_frontmatter"]:
            t.add_row("[red]no frontmatter[/red]", o)
        for o in h["orphans"]:
            t.add_row("[yellow]orphan[/yellow]", o)
        for b in h["broken_links"]:
            t.add_row("[red]broken link[/red]", b)
        out.print(Panel(t, title=f"Doc Health ({issues} issue{'s' if issues != 1 else ''})", border_style="red"))


# ── command ───────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def dashboard(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of the rendered view."),
) -> None:
    """Render a one-screen overview of project state from docs/."""
    docs = find_docs_dir()
    if docs is None:
        err_console.print("[bold red]No docs/ found.[/bold red]")
        err_console.print("[dim]Hint: run /docs-init (or tai setup) to bootstrap the docs tree.[/dim]")
        raise typer.Exit(1)

    as_json = json_output
    try:
        app_ctx = get_ctx(ctx)
        as_json = as_json or app_ctx.json_output
    except Exception:
        pass

    data = build_dashboard(docs)
    if as_json:
        console.print_json(_json.dumps(data.to_dict()))
    else:
        render(data, console)
