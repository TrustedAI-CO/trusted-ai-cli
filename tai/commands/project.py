"""tai project — link a repo to its Notion project and manage tool bindings."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from tai.core.errors import ProjectError, handle_error
from tai.core.http import build_client
from tai.core.project import ProjectManifest, find_repo_root, load_manifest, save_manifest

app = typer.Typer(name="project", help="Manage project tool bindings.")
console = Console()
err_console = Console(stderr=True)

_TOOL_FIELDS = {
    "github": "github_repo",
    "drive": "drive_folder",
    "chat": "gchat_space",
}

_TOOL_LABELS = {
    "github_repo": "GitHub",
    "drive_folder": "Drive",
    "gchat_space": "GChat",
    "notion_url": "Notion",
    "status": "Status",
    "phase": "Phase",
}


def _require_manifest(ctx: typer.Context):
    root = find_repo_root()
    if root is None:
        err_console.print("[bold red]Error:[/bold red] Not inside a git repository.")
        raise typer.Exit(1)

    manifest = load_manifest(root)
    if manifest is None:
        err_console.print(
            "[bold red]Error:[/bold red] This repo is not linked to a project.\n"
            "[dim]Hint: Run: tai project link <notion-url>[/dim]"
        )
        raise typer.Exit(1)

    return root, manifest


def _fetch_project(ctx: typer.Context, page_id: str) -> dict:
    client = build_client(ctx.obj)
    resp = client.get(f"/projects/{page_id}")
    return resp.json()


def _patch_project(ctx: typer.Context, page_id: str, payload: dict) -> dict:
    client = build_client(ctx.obj)
    resp = client.patch(f"/projects/{page_id}", json=payload)
    return resp.json()


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


@app.command()
def link(
    ctx: typer.Context,
    notion_url: Annotated[str, typer.Argument(help="Notion project page URL or ID.")],
) -> None:
    """Link this repo to a Notion project page."""
    root = find_repo_root()
    if root is None:
        err_console.print("[bold red]Error:[/bold red] Not inside a git repository.")
        raise typer.Exit(1)

    try:
        manifest = ProjectManifest(notion_page=notion_url)
    except Exception:
        err_console.print(
            "[bold red]Error:[/bold red] Could not extract a Notion page ID from the provided value.\n"
            "[dim]Hint: Pass the full Notion page URL, e.g. https://www.notion.so/My-Project-abc123[/dim]"
        )
        raise typer.Exit(1)

    save_manifest(manifest, root)
    console.print(f"[green]Linked[/green] → notion page [cyan]{manifest.notion_page}[/cyan]")
    console.print("[dim]Run: tai project status[/dim]")


@app.command()
def status(ctx: typer.Context) -> None:
    """Show all tool bindings for this project."""
    root, manifest = _require_manifest(ctx)
    data = _fetch_project(ctx, manifest.notion_page)
    _print_project(data)


@app.command()
def set(
    ctx: typer.Context,
    tool: Annotated[str, typer.Argument(help="Tool to bind: github | drive | chat")],
    value: Annotated[str, typer.Argument(help="URL or identifier to bind.")],
) -> None:
    """Update a tool binding for this project."""
    if tool not in _TOOL_FIELDS:
        valid = " | ".join(_TOOL_FIELDS)
        err_console.print(
            f"[bold red]Error:[/bold red] Unknown tool '{tool}'. Valid options: {valid}"
        )
        raise typer.Exit(1)

    _, manifest = _require_manifest(ctx)
    field = _TOOL_FIELDS[tool]
    data = _patch_project(ctx, manifest.notion_page, {field: value})
    console.print(f"[green]Updated[/green] {_TOOL_LABELS.get(field, tool)} → [cyan]{value}[/cyan]")
    _print_project(data)
