"""tai project tasks — list and manage Notion tasks for the current project."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from tai.core.errors import ApiError, ExitCode, handle_error
from tai.core.http import build_client
from tai.core.project import find_repo_root, load_manifest
from tai.core.prompt import is_interactive, search_select

app = typer.Typer(name="tasks", help="Manage project tasks.")
console = Console()
err_console = Console(stderr=True)


def _require_manifest(ctx: typer.Context):
    root = find_repo_root()
    if root is None:
        err_console.print("[bold red]Error:[/bold red] Not inside a git repository.")
        raise typer.Exit(1)

    manifest = load_manifest(root)
    if manifest is None:
        err_console.print(
            "[bold red]Error:[/bold red] This repo is not linked to a project.\n"
            "[dim]Hint: Run: tai project link[/dim]"
        )
        raise typer.Exit(1)

    return manifest


def _fetch_tasks(ctx: typer.Context, project_id: str) -> list[dict]:
    try:
        client = build_client(ctx.obj)
        return client.get(f"/projects/{project_id}/tasks").json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(e.exit_code)


def _resolve_short_id(tasks: list[dict], short_id: str) -> str:
    matches = [t for t in tasks if t["short_id"].startswith(short_id)]
    if not matches:
        err_console.print(f"[bold red]Error:[/bold red] No task found with ID starting '{short_id}'.")
        raise typer.Exit(ExitCode.NOT_FOUND)
    if len(matches) > 1:
        err_console.print(
            f"[bold red]Error:[/bold red] Ambiguous ID '{short_id}' — {len(matches)} tasks match. "
            "Provide more characters."
        )
        raise typer.Exit(ExitCode.CONFLICT)
    return matches[0]["task_id"]


def _print_table(tasks: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Task")
    table.add_column("Description", style="dim")
    table.add_column("Status")
    table.add_column("Due", style="dim")
    table.add_column("Assignee", style="dim")

    for task in tasks:
        status = task.get("status") or "—"
        style = "green" if status == "Done" else ""
        table.add_row(
            task["short_id"],
            task["name"],
            task.get("description") or "—",
            f"[{style}]{status}[/{style}]" if style else status,
            task.get("due_date") or "—",
            task.get("assignee") or "—",
        )

    console.print(table)


# ── commands ──────────────────────────────────────────────────────────────────


@app.callback(invoke_without_command=True)
def list_tasks(
    ctx: typer.Context,
    all_projects: bool = typer.Option(False, "-a", "--all", help="Show tasks across all projects."),
    limit: int | None = typer.Option(None, "-n", "--limit", help="Limit number of results."),
    filter_text: str | None = typer.Option(None, "-f", "--filter", help="Filter by name (case-insensitive substring)."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Output task names only, one per line."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List tasks for the current project (or all with -a)."""
    if ctx.invoked_subcommand is not None:
        return

    if all_projects:
        try:
            client = build_client(ctx.obj)
            tasks = client.get("/tasks").json()
        except ApiError as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(e.exit_code)
    else:
        manifest = _require_manifest(ctx)
        tasks = _fetch_tasks(ctx, manifest.notion_page)

    if filter_text:
        tasks = [t for t in tasks if filter_text.lower() in (t.get("name") or "").lower()]
    if limit is not None:
        tasks = tasks[:limit]

    if not tasks:
        msg = f"[dim]No tasks matching '{filter_text}'.[/dim]" if filter_text else "[dim]No tasks found.[/dim]"
        console.print(msg)
        return

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    if json_output:
        console.print_json(json.dumps(tasks))
    elif quiet:
        for task in tasks:
            print(task["name"])
    else:
        _print_table(tasks)


@app.command()
def add(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Create a new task for the current project."""
    manifest = _require_manifest(ctx)
    name = typer.prompt("Task name")

    try:
        client = build_client(ctx.obj)
        task = client.post(
            f"/projects/{manifest.notion_page}/tasks",
            json={"name": name},
        ).json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(e.exit_code)

    if json_flag or getattr(ctx.obj, "json_output", False):
        console.print_json(json.dumps(task))
    else:
        console.print(f"[green]Created[/green] {task['short_id']} {task['name']}")


def _task_row(task: dict) -> str:
    short_id = task.get("short_id", "")
    name = (task.get("name") or "")[:40].ljust(40)
    status = (task.get("status") or "—")[:14].ljust(14)
    assignee = task.get("assignee") or "—"
    return f"{short_id}  {name}  {status}  {assignee}"


@app.command()
def done(
    ctx: typer.Context,
    short_id: Annotated[str | None, typer.Argument(help="Short task ID (or prefix). Omit for interactive picker.")] = None,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Mark a task as Done."""
    manifest = _require_manifest(ctx)
    tasks = _fetch_tasks(ctx, manifest.notion_page)

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        raise typer.Exit(0)

    open_tasks = [t for t in tasks if t.get("status") != "Done"]

    if short_id is not None:
        task_id = _resolve_short_id(tasks, short_id)
    elif is_interactive():
        chosen = search_select("Mark as done:", open_tasks, label_fn=_task_row)
        if chosen is None:
            raise typer.Exit(0)
        task_id = chosen["task_id"]
    else:
        err_console.print("[bold red]Error:[/bold red] No task ID given and stdin is not interactive.")
        err_console.print("[dim]Hint: tai tasks done <short_id>[/dim]")
        raise typer.Exit(ExitCode.USAGE)

    try:
        client = build_client(ctx.obj)
        task = client.patch(
            f"/projects/{manifest.notion_page}/tasks/{task_id}",
            json={"status": "Done"},
        ).json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(e.exit_code)

    if json_flag or getattr(ctx.obj, "json_output", False):
        console.print_json(json.dumps(task))
    else:
        console.print(f"[green]Done[/green] {task['short_id']} {task['name']}")
