"""tai gate — clear a gate from the terminal: approve a spec, accept an ADR, resolve a
REVIEW item.

Implements SPEC-gates-action. The ONE surface that writes to gated source docs, so the
invariants are strict:
- INV1 human-initiated only (the invocation IS the authorization; never agent-auto).
- INV2 flips the status field (+ stamps approved_at) and commits — never edits content.
- INV3 refuses invalid transitions (no write).
- INV4 every success = exactly one audited git commit.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from tai.commands.dashboard import (
    find_docs_dir, find_doc_by_id, parse_frontmatter, _read, _doc_rows,
)

app = typer.Typer(name="gate", help="Clear a gate: approve a spec, accept an ADR, resolve a REVIEW item.")
console = Console()
err_console = Console(stderr=True)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _require_docs() -> Path:
    docs = find_docs_dir()
    if docs is None:
        err_console.print("[bold red]No docs/ found.[/bold red]")
        raise typer.Exit(1)
    return docs


def _not_found(docs: Path, doc_id: str) -> "typer.Exit":
    err_console.print(f"[bold red]No doc with id '{doc_id}'.[/bold red]")
    near = [r.id for r in _doc_rows(docs) if doc_id.lower() in r.id.lower()][:3]
    if near:
        err_console.print(f"[dim]Did you mean: {', '.join(near)}?[/dim]")
    return typer.Exit(1)


def _confirm(action: str, target: str, transition: str, yes: bool) -> None:
    console.print(f"[bold]{action}[/bold] {target}: {transition}")
    if not yes and not typer.confirm("Proceed?"):
        err_console.print("[dim]aborted — no change.[/dim]")
        raise typer.Exit(1)


def _git_commit(repo: Path, rel: str, message: str) -> None:
    """Stage + commit ONLY `rel` (pathspec commit ignores anything else staged)."""
    subprocess.run(["git", "-C", str(repo), "add", "--", rel], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", message, "--", rel],
                   check=True, capture_output=True)


def _write_commit_or_rollback(path: Path, docs: Path, original: str, updated: str, message: str) -> None:
    """Write `updated`, commit just this file; on any commit failure restore `original`
    so a failed action never leaves an uncommitted source mutation (INV4)."""
    path.write_text(updated, encoding="utf-8")
    rel = str(path.relative_to(docs.parent))
    try:
        _git_commit(docs.parent, rel, message)
    except subprocess.CalledProcessError as exc:
        path.write_text(original, encoding="utf-8")  # rollback the mutation
        err_console.print("[bold red]Commit failed — reverted, no change.[/bold red]")
        detail = (exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")).strip()
        if detail:
            err_console.print(f"[dim]{detail.splitlines()[-1]}[/dim]")
        raise typer.Exit(1)


def _flip_status(text: str, current: str, new: str, stamp_at: Optional[str]) -> Optional[str]:
    """Return new file text with `status: current` → `status: new` (and approved_at stamped),
    touching ONLY those frontmatter lines. None if the status line isn't `current` (refuse)."""
    if not text.startswith("---"):
        return None
    head, sep, body = text.partition("\n---")  # frontmatter is text up to the closing ---
    if not re.search(rf"(?m)^status:\s*{re.escape(current)}\s*$", head):
        return None
    head = re.sub(rf"(?m)^status:\s*{re.escape(current)}\s*$", f"status: {new}", head, count=1)
    if stamp_at is not None:
        if re.search(r"(?m)^approved_at:", head):
            head = re.sub(r"(?m)^approved_at:.*$", f"approved_at: {stamp_at}", head, count=1)
        else:  # insert right after the status line
            head = re.sub(r"(?m)^(status:.*)$", rf"\1\napproved_at: {stamp_at}", head, count=1)
    return head + sep + body


def _require_type(path: Path, expected: str, doc_id: str) -> None:
    actual = parse_frontmatter(_read(path)).get("type")
    if actual != expected:
        err_console.print(f"[bold red]{doc_id} is a '{actual}', not a '{expected}'.[/bold red] No change.")
        raise typer.Exit(1)


def _apply(path: Path, docs: Path, current: str, new: str, stamp: bool, label: str, doc_id: str) -> None:
    text = _read(path)
    updated = _flip_status(text, current, new, _now() if stamp else None)
    if updated is None:
        cur = parse_frontmatter(text).get("status")
        err_console.print(f"[bold red]{doc_id} is '{cur}', not '{current}'.[/bold red] No change.")
        raise typer.Exit(1)
    _write_commit_or_rollback(path, docs, text, updated, f"gate({label}): {doc_id} → {new}")
    console.print(f"[green]✓[/green] {doc_id}: {current} → {new} (committed)")


@app.command("approve")
def approve(spec_id: str = typer.Argument(...), yes: bool = typer.Option(False, "--yes")) -> None:
    """GATE C — approve a spec (draft → approved, stamps approved_at)."""
    docs = _require_docs()
    path = find_doc_by_id(docs, spec_id)
    if path is None:
        raise _not_found(docs, spec_id)
    _require_type(path, "spec", spec_id)
    _confirm("approve", spec_id, "draft → approved", yes)
    _apply(path, docs, "draft", "approved", stamp=True, label="C", doc_id=spec_id)


@app.command("accept")
def accept(adr_id: str = typer.Argument(...), yes: bool = typer.Option(False, "--yes")) -> None:
    """GATE B — accept an ADR (proposed → accepted)."""
    docs = _require_docs()
    path = find_doc_by_id(docs, adr_id)
    if path is None:
        raise _not_found(docs, adr_id)
    _require_type(path, "decision", adr_id)
    _confirm("accept", adr_id, "proposed → accepted", yes)
    _apply(path, docs, "proposed", "accepted", stamp=False, label="B", doc_id=adr_id)


@app.command("resolve")
def resolve(review_id: str = typer.Argument(...), yes: bool = typer.Option(False, "--yes")) -> None:
    """REVIEW — mark an open PENDING attention-log item resolved."""
    docs = _require_docs()
    review = docs / "REVIEW.md"
    text = _read(review)
    # locate the [REVIEW-id] block and confirm it's PENDING in the open section
    open_section = text.split("## Resolved", 1)[0]
    block_re = re.compile(rf"(?ms)^### \[?{re.escape(review_id)}\]?.*?(?=^### |\Z)")
    m = block_re.search(open_section)
    if not m or not re.search(r"(?i)status:\**\s*pending", m.group(0)):
        err_console.print(f"[bold red]{review_id} not found as an open PENDING item.[/bold red]")
        raise typer.Exit(1)
    _confirm("resolve", review_id, "PENDING → RESOLVED", yes)
    new_block = re.sub(r"(?i)(status:\**\s*)pending", r"\1RESOLVED", m.group(0), count=1)
    updated = text[:m.start()] + new_block + text[m.end():]
    _write_commit_or_rollback(review, docs, text, updated, f"gate(review): {review_id} → resolved")
    console.print(f"[green]✓[/green] {review_id}: PENDING → RESOLVED (committed)")
