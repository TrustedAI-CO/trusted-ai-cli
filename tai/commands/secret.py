"""tai secret — set, get, list, rotate, delete, exec."""

import json
import os
import subprocess
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from tai.core import keystore
from tai.core.context import get_ctx
from tai.core.errors import handle_error, TaiError

app = typer.Typer(name="secret", help="Manage secrets stored in the system keychain.")
console = Console()
err_console = Console(stderr=True)


@app.command("set")
def set_secret(
    ctx: typer.Context,
    name: str = typer.Argument(help="Secret name (e.g. OPENAI_API_KEY)"),
):
    """Store a secret. Value is prompted interactively (never passed as a flag)."""
    app_ctx = get_ctx(ctx)
    value = typer.prompt(f"Value for {name}", hide_input=True, confirmation_prompt=True)
    try:
        keystore.store(app_ctx.profile, name, value)
        console.print(f"[green]✓[/green] Secret [bold]{name}[/bold] stored.")
    except TaiError as e:
        handle_error(e)


@app.command("get")
def get_secret(
    ctx: typer.Context,
    name: str = typer.Argument(help="Secret name"),
    export: bool = typer.Option(False, "--export", help="Print as: export NAME=value"),
):
    """Retrieve a secret value."""
    app_ctx = get_ctx(ctx)
    try:
        value = keystore.retrieve(app_ctx.profile, name)
        if export:
            console.print(f"export {name}={value}")
        elif app_ctx.json_output:
            console.print_json(json.dumps({"name": name, "value": value}))
        else:
            console.print(value)
    except TaiError as e:
        handle_error(e)


@app.command("list")
def list_secrets(ctx: typer.Context):
    """List all secret names for the current profile (values are never shown)."""
    app_ctx = get_ctx(ctx)
    names = keystore.list_names(app_ctx.profile)
    if not names:
        console.print(f"No secrets stored for profile [bold]{app_ctx.profile}[/bold].")
        return

    if app_ctx.json_output:
        console.print_json(json.dumps({"profile": app_ctx.profile, "secrets": names}))
        return

    table = Table(title=f"Secrets — profile: {app_ctx.profile}")
    table.add_column("Name", style="bold cyan")
    for n in names:
        table.add_row(n)
    console.print(table)


@app.command()
def rotate(
    ctx: typer.Context,
    name: str = typer.Argument(help="Secret name to rotate"),
):
    """Replace a secret with a new value (atomic update)."""
    app_ctx = get_ctx(ctx)
    value = typer.prompt(f"New value for {name}", hide_input=True, confirmation_prompt=True)
    try:
        keystore.rotate(app_ctx.profile, name, value)
        console.print(f"[green]✓[/green] Secret [bold]{name}[/bold] rotated.")
    except TaiError as e:
        handle_error(e)


@app.command()
def delete(
    ctx: typer.Context,
    name: str = typer.Argument(help="Secret name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a secret."""
    app_ctx = get_ctx(ctx)
    if not force:
        typer.confirm(f"Delete secret '{name}'?", abort=True)
    try:
        keystore.delete(app_ctx.profile, name)
        console.print(f"[green]✓[/green] Secret [bold]{name}[/bold] deleted.")
    except TaiError as e:
        handle_error(e)


@app.command("exec")
def exec_with_secrets(
    ctx: typer.Context,
    command: list[str] = typer.Argument(help="Command to run with secrets injected as env vars"),
):
    """Run a command with all profile secrets injected as environment variables.

    Example: tai secret exec -- python my_script.py
    """
    app_ctx = get_ctx(ctx)
    names = keystore.list_names(app_ctx.profile)
    env = os.environ.copy()
    for name in names:
        try:
            env[name] = keystore.retrieve(app_ctx.profile, name)
        except TaiError:
            pass

    if not command:
        err_console.print("No command specified.")
        raise typer.Exit(1)

    result = subprocess.run(command, env=env)
    raise typer.Exit(result.returncode)
