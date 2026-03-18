"""tai project — manage Notion project bindings."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from tai.core.errors import ApiError, ExitCode, handle_error
from tai.core.http import build_client
from tai.core.project import ProjectManifest, find_repo_root, load_manifest, save_manifest
from tai.core.prompt import is_interactive, search_select

app = typer.Typer(name="project", help="Manage project tool bindings.")
console = Console()
err_console = Console(stderr=True)

_OPEN_FIELDS = {
    "github": "github_repo",
    "drive": "drive_folder",
    "chat": "gchat_space",
    "notion": "notion_url",
}

_TOOL_LABELS = {
    "github_repo": "GitHub",
    "drive_folder": "Drive",
    "gchat_space": "GChat",
    "notion_url": "Notion",
    "status": "Status",
    "phase": "Phase",
}


def _project_row(p: dict) -> str:
    name   = p.get("name", "")[:30].ljust(30)
    phase  = (p.get("phase") or "—")[:12].ljust(12)
    status = (p.get("status") or "—")[:14].ljust(14)
    client = p.get("client") or "—"
    return f"{name}  {phase}  {status}  {client}"


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

    return root, manifest


def _fetch_project(ctx: typer.Context, page_id: str) -> dict:
    try:
        client = build_client(ctx.obj)
        return client.get(f"/projects/{page_id}").json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)



def _print_project(data: dict) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column()

    table.add_row("Name", f"[bold]{data.get('name', '')}[/bold]")
    table.add_row("Notion", data.get("notion_url") or "[dim]—[/dim]")
    table.add_row("Status", data.get("status") or "[dim]—[/dim]")
    table.add_row("Phase", data.get("phase") or "[dim]—[/dim]")
    table.add_row("GitHub", data.get("github_repo") or "[dim]—[/dim]")
    table.add_row("Drive", data.get("drive_folder") or "[dim]—[/dim]")
    table.add_row("GChat", data.get("gchat_space") or "[dim]—[/dim]")

    console.print(table)


# ── commands ──────────────────────────────────────────────────────────────────


def link(ctx: typer.Context) -> None:
    """Interactively pick a project and link this repo to it."""
    if not is_interactive():
        err_console.print("[bold red]Error:[/bold red] tai link requires an interactive terminal.")
        err_console.print("[dim]Hint: Run in a terminal, not in a script or agent.[/dim]")
        raise typer.Exit(ExitCode.USAGE)

    root = find_repo_root()
    if root is None:
        err_console.print("[bold red]Error:[/bold red] Not inside a git repository.")
        raise typer.Exit(1)

    try:
        client = build_client(ctx.obj)
        projects = client.get("/projects").json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(e.exit_code)

    if not projects:
        err_console.print("[yellow]No projects found.[/yellow]")
        raise typer.Exit(1)

    chosen = search_select("Project:", projects, label_fn=_project_row)

    if chosen is None:
        raise typer.Exit(0)
    manifest = ProjectManifest(notion_page=chosen["notion_page_id"])
    save_manifest(manifest, root)
    console.print(f"\n[green]Linked[/green] → [bold]{chosen['name']}[/bold]")
    console.print("[dim]Run: tai project status[/dim]")


def unlink(ctx: typer.Context) -> None:
    """Remove the project link from this repo."""
    root = find_repo_root()
    if root is None:
        err_console.print("[bold red]Error:[/bold red] Not inside a git repository.")
        raise typer.Exit(1)

    tai_toml = root / ".tai.toml"
    if not tai_toml.exists():
        err_console.print("[yellow]This repo is not linked to any project.[/yellow]")
        raise typer.Exit(0)

    tai_toml.unlink()
    console.print("[green]Unlinked[/green] — .tai.toml removed.")



def open_tool(
    ctx: typer.Context,
    tool: Annotated[str, typer.Argument(help="Tool to open: github | drive | chat | notion")],
) -> None:
    """Open a linked resource in the browser."""
    if tool not in _OPEN_FIELDS:
        valid = " | ".join(_OPEN_FIELDS)
        err_console.print(
            f"[bold red]Error:[/bold red] Unknown tool '{tool}'. Valid options: {valid}"
        )
        raise typer.Exit(1)

    _, manifest = _require_manifest(ctx)
    data = _fetch_project(ctx, manifest.notion_page)
    field = _OPEN_FIELDS[tool]
    url = data.get(field)

    if not url:
        err_console.print(
            f"[bold red]Error:[/bold red] No {_TOOL_LABELS.get(field, tool)} URL set for this project.\n"
            f"[dim]Hint: Update it directly in Notion.[/dim]"
        )
        raise typer.Exit(1)

    typer.launch(url)
    console.print(f"[green]Opening[/green] {_TOOL_LABELS.get(field, tool)} → [cyan]{url}[/cyan]")


@app.command()
def new(ctx: typer.Context) -> None:
    """Create a new project in Notion and link this repo to it."""
    root = find_repo_root()
    if root is None:
        err_console.print("[bold red]Error:[/bold red] Not inside a git repository.")
        raise typer.Exit(1)

    name = typer.prompt("Project name")
    description = typer.prompt("Description", default="")
    category = typer.prompt(
        "Category",
        default="Development",
        prompt_suffix=" [Development/Consulting/Research/Internal/Recruitment]: ",
    )

    try:
        client = build_client(ctx.obj)
        payload = {"name": name}
        if description:
            payload["description"] = description
        if category:
            payload["category"] = category
        created = client.post("/projects", json=payload).json()
    except ApiError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)

    manifest = ProjectManifest(notion_page=created["notion_page_id"])
    save_manifest(manifest, root)
    console.print(f"\n[green]Created[/green] → [bold]{created['name']}[/bold]")
    console.print(f"[dim]Notion: {created['notion_url']}[/dim]")
    console.print("[dim]Run: tai project status[/dim]")


@app.command()
def status(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show all tool bindings for this project."""
    root, manifest = _require_manifest(ctx)
    data = _fetch_project(ctx, manifest.notion_page)
    if json_flag or getattr(ctx.obj, "json_output", False):
        console.print_json(json.dumps(data))
    else:
        _print_project(data)
