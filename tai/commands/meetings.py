"""tai meetings — list and manage Notion meetings for the current project."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from tai.core.errors import ApiError
from tai.core.http import build_client
from tai.core.project import find_repo_root, load_manifest
from tai.core.prompt import search_select

app = typer.Typer(name="meetings", help="Manage project meetings.")
console = Console()
err_console = Console(stderr=True)

_NOTION_PAGE_BASE = "https://notion.so/"
_TYPE_OPTIONS = ["Colab", "Sale meeting", "External meeting", "Project meeting", "Review", "Team meeting"]


def _require_manifest(ctx: typer.Context):
    root = find_repo_root()
    if root is None:
        err_console.print("[bold red]Error:[/bold red] Not inside a git repository.")
        raise typer.Exit(1)

    manifest = load_manifest(root)
    if manifest is None:
        err_console.print(
            "[bold red]Error:[/bold red] This repo is not linked to a project.\n"
            "[dim]Hint: Run: tai link[/dim]"
        )
        raise typer.Exit(1)

    return manifest


def _fetch_meetings(ctx: typer.Context, project_id: str) -> list[dict]:
    try:
        client = build_client(ctx.obj)
        return client.get(f"/projects/{project_id}/meetings").json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


def _resolve_short_id(meetings: list[dict], short_id: str) -> str:
    matches = [m for m in meetings if m["short_id"].startswith(short_id)]
    if not matches:
        err_console.print(f"[bold red]Error:[/bold red] No meeting found with ID starting '{short_id}'.")
        raise typer.Exit(1)
    if len(matches) > 1:
        err_console.print(
            f"[bold red]Error:[/bold red] Ambiguous ID '{short_id}' — {len(matches)} meetings match. "
            "Provide more characters."
        )
        raise typer.Exit(1)
    return matches[0]["meeting_id"]


def _meeting_row(meeting: dict) -> str:
    short_id = meeting.get("short_id", "")
    title = (meeting.get("title") or "")[:40].ljust(40)
    date = (meeting.get("date") or "—")[:16].ljust(16)
    lead = meeting.get("lead") or "—"
    return f"{short_id}  {title}  {date}  {lead}"


# ── commands ──────────────────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def list_meetings(
    ctx: typer.Context,
    all_projects: bool = typer.Option(False, "-a", "--all", help="Show meetings across all projects."),
    limit: int | None = typer.Option(None, "-n", "--limit", help="Limit number of results."),
    filter_text: str | None = typer.Option(None, "-f", "--filter", help="Filter by title (case-insensitive substring)."),
) -> None:
    """List meetings for the current project (or all with -a)."""
    if ctx.invoked_subcommand is not None:
        return

    if all_projects:
        try:
            client = build_client(ctx.obj)
            meetings = client.get("/meetings").json()
        except ApiError as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)
    else:
        manifest = _require_manifest(ctx)
        meetings = _fetch_meetings(ctx, manifest.notion_page)

    if filter_text:
        meetings = [m for m in meetings if filter_text.lower() in (m.get("title") or "").lower()]
    if limit is not None:
        meetings = meetings[:limit]

    if not meetings:
        msg = f"[dim]No meetings matching '{filter_text}'.[/dim]" if filter_text else "[dim]No meetings found.[/dim]"
        console.print(msg)
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Meeting")
    table.add_column("Date", style="dim")

    for meeting in meetings:
        notion_url = meeting.get("notion_url") or ""
        short_id = (
            f"[link={notion_url}]{meeting['short_id']}[/link]" if notion_url else meeting["short_id"]
        )
        table.add_row(
            short_id,
            meeting["title"],
            meeting.get("date") or "—",
        )

    console.print(table)


@app.command()
def add(ctx: typer.Context) -> None:
    """Create a new meeting for the current project."""
    manifest = _require_manifest(ctx)
    title = typer.prompt("Meeting name")
    date = typer.prompt("Date (YYYY-MM-DD or YYYY-MM-DDTHH:MM)", default="")
    meeting_type = typer.prompt(
        "Type",
        default="",
        prompt_suffix=f" [{'/'.join(_TYPE_OPTIONS)}]: ",
    )

    payload: dict = {"title": title}
    if date:
        payload["date"] = date
    if meeting_type:
        payload["meeting_type"] = [meeting_type]

    try:
        client = build_client(ctx.obj)
        meeting = client.post(
            f"/projects/{manifest.notion_page}/meetings",
            json=payload,
        ).json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    console.print(f"[green]Created[/green] {meeting['short_id']} {meeting['title']}")


@app.command(name="open")
def open_meeting(
    ctx: typer.Context,
    short_id: Annotated[
        str | None,
        typer.Argument(help="Short meeting ID (or prefix). Omit for interactive picker."),
    ] = None,
) -> None:
    """Open a meeting's Notion page in the browser."""
    manifest = _require_manifest(ctx)
    meetings = _fetch_meetings(ctx, manifest.notion_page)

    if not meetings:
        console.print("[dim]No meetings found.[/dim]")
        raise typer.Exit(0)

    if short_id is not None:
        meeting_id = _resolve_short_id(meetings, short_id)
        meeting = next(m for m in meetings if m["meeting_id"] == meeting_id)
    else:
        meeting = search_select("Open meeting:", meetings, label_fn=_meeting_row)
        if meeting is None:
            raise typer.Exit(0)

    url = meeting.get("notion_url") or f"{_NOTION_PAGE_BASE}{meeting['meeting_id']}"
    typer.launch(url)
    console.print(f"[green]Opening[/green] Notion → [cyan]{url}[/cyan]")
