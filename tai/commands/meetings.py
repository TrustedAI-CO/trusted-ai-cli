"""tai meetings — list and manage Notion meetings for the current project."""

from __future__ import annotations

import json

import typer
from rich.console import Console

from tai.core.errors import ApiError, ExitCode
from tai.core.http import build_client
from tai.core.project import find_repo_root, load_manifest
from tai.core.prompt import is_interactive, search_select

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
        raise typer.Exit(e.exit_code)


def _resolve_short_id(meetings: list[dict], short_id: str) -> dict:
    matches = [m for m in meetings if m["short_id"].startswith(short_id)]
    if not matches:
        err_console.print(f"[bold red]Error:[/bold red] No meeting found with ID starting '{short_id}'.")
        raise typer.Exit(ExitCode.NOT_FOUND)
    if len(matches) > 1:
        err_console.print(
            f"[bold red]Error:[/bold red] Ambiguous ID '{short_id}' — {len(matches)} meetings match. "
            "Provide more characters."
        )
        raise typer.Exit(ExitCode.CONFLICT)
    return matches[0]


def _meeting_row(meeting: dict) -> str:
    short_id = meeting.get("short_id", "")
    title = (meeting.get("title") or "")[:40].ljust(40)
    date = (meeting.get("date") or "—")[:10].ljust(10)
    return f"{short_id}  {title}  {date}"


def _open(meeting: dict) -> None:
    url = meeting.get("notion_url") or f"{_NOTION_PAGE_BASE}{meeting['meeting_id']}"
    typer.launch(url)
    console.print(f"[green]Opening[/green] [bold]{meeting['title']}[/bold] → [cyan]{url}[/cyan]")


# ── commands ──────────────────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def list_meetings(
    ctx: typer.Context,
    all_projects: bool = typer.Option(False, "-a", "--all", help="Show meetings across all projects."),
    limit: int | None = typer.Option(None, "-n", "--limit", help="Limit number of results."),
    filter_text: str | None = typer.Option(None, "-f", "--filter", help="Filter by title (case-insensitive substring)."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Output meeting titles only, one per line."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Pick a meeting to open in Notion (interactive), or list meetings (non-interactive/--json/--quiet)."""
    if ctx.invoked_subcommand is not None:
        return

    if all_projects:
        try:
            client = build_client(ctx.obj)
            meetings = client.get("/meetings").json()
        except ApiError as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(e.exit_code)
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

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    if json_output:
        console.print_json(json.dumps(meetings))
    elif quiet:
        for m in meetings:
            print(m["title"])
    elif is_interactive():
        chosen = search_select("Meeting:", meetings, label_fn=_meeting_row)
        if chosen is None:
            raise typer.Exit(0)
        _open(chosen)
    else:
        # Non-interactive fallback: print plain list to stdout
        for m in meetings:
            date = m.get("date") or "—"
            print(f"{m['short_id']}  {m['title']}  {date}")


@app.command()
def add(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
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
        raise typer.Exit(e.exit_code)

    if json_flag or getattr(ctx.obj, "json_output", False):
        console.print_json(json.dumps(meeting))
    else:
        console.print(f"[green]Created[/green] {meeting['short_id']} {meeting['title']}")
