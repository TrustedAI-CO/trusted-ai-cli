"""tai claude — manage Claude Code authentication."""

from __future__ import annotations

import shutil
import subprocess
import sys

import typer
from rich.console import Console

from tai.core.context import get_ctx

app = typer.Typer(name="claude", help="Manage Claude Code authentication.")
console = Console()
err_console = Console(stderr=True)

_URL_PREFIX = "If the browser didn't open, visit: "


@app.command()
def login(ctx: typer.Context):
    """Authenticate Claude Code via browser OAuth.

    Prints the login URL and waits for you to paste the code back.
    Share the URL with an admin if you can't open a browser yourself.
    """
    claude_bin = shutil.which("claude")
    if not claude_bin:
        err_console.print("[bold red]Error:[/bold red] 'claude' not found in PATH.")
        err_console.print("[dim]Hint: Install Claude Code — https://claude.ai/code[/dim]")
        raise typer.Exit(1)

    console.print("Starting Claude Code authentication…")

    proc = subprocess.Popen(
        [claude_bin, "auth", "login"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # merge stderr into stdout so we catch all output
        stdin=sys.stdin,
        text=True,
        bufsize=1,
    )

    assert proc.stdout is not None
    url_shown = False

    for line in proc.stdout:
        line_stripped = line.rstrip("\n")

        if _URL_PREFIX in line_stripped:
            url = line_stripped.split(_URL_PREFIX, 1)[1].strip()
            console.print()
            console.print("[bold]Login URL:[/bold]")
            console.print(f"  [cyan]{url}[/cyan]")
            console.print()
            console.print("[dim]Open the URL above in a browser, complete sign-in,[/dim]")
            console.print("[dim]then paste the code shown on the success page below.[/dim]")
            console.print()
            url_shown = True
        elif "Opening browser to sign in" in line_stripped:
            # suppress — we show our own message
            pass
        else:
            # forward all other output (including the code prompt) as-is
            sys.stdout.write(line)
            sys.stdout.flush()

    proc.wait()

    if proc.returncode == 0:
        console.print()
        console.print("[green]✓[/green] Claude Code authenticated successfully.")
    else:
        console.print()
        err_console.print("[bold red]Authentication failed.[/bold red]")
        raise typer.Exit(proc.returncode)


@app.command()
def logout(ctx: typer.Context):
    """Sign out of Claude Code."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        err_console.print("[bold red]Error:[/bold red] 'claude' not found in PATH.")
        raise typer.Exit(1)

    result = subprocess.run([claude_bin, "auth", "logout"])
    raise typer.Exit(result.returncode)


@app.command()
def status(ctx: typer.Context):
    """Show Claude Code authentication status."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        err_console.print("[bold red]Error:[/bold red] 'claude' not found in PATH.")
        raise typer.Exit(1)

    result = subprocess.run([claude_bin, "auth", "status"])
    raise typer.Exit(result.returncode)
