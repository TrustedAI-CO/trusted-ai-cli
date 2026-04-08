"""tai browser — install and manage the gstack browse tool."""

from __future__ import annotations

import json

import typer
from rich.console import Console

from tai.core.browser_setup import check_bun, get_browser_status
from tai.core.errors import BrowserError, handle_error

app = typer.Typer(name="browser", help="Install and manage the gstack browse tool.")

console = Console()
err_console = Console(stderr=True)


@app.command("install")
def browser_install(
    ctx: typer.Context,
    ref: str = typer.Option("main", "--ref", help="Git ref to install (branch, tag, or commit)."),
) -> None:
    """Download, build, and install the gstack browse binary."""
    json_output = getattr(ctx.obj, "json_output", False)

    try:
        with console.status("Installing gstack browse tool..."):
            from tai.core.browser_setup import install_browse

            binary_path = install_browse(ref=ref)

        if json_output:
            console.print_json(json.dumps({
                "status": "ok",
                "binary_path": str(binary_path),
            }))
        else:
            console.print(f"Binary path: {binary_path}")
            console.print("[green]Browse tool installed successfully.[/green]")

    except BrowserError as exc:
        handle_error(exc)


@app.command("status")
def browser_status(
    ctx: typer.Context,
) -> None:
    """Show installation status of the browse tool."""
    json_output = getattr(ctx.obj, "json_output", False)
    status = get_browser_status()

    if json_output:
        console.print_json(json.dumps({
            "installed": status.installed,
            "binary_path": str(status.binary_path) if status.binary_path else None,
            "version": status.version,
        }))
    else:
        bun_available = check_bun()
        console.print(f"Bun available: {'[green]yes[/green]' if bun_available else '[red]no[/red]'}")
        console.print(
            f"Browse binary: {status.binary_path or '[dim]not installed[/dim]'}"
        )
        console.print(f"Version:       {status.version or '[dim]unknown[/dim]'}")
