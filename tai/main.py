"""tai — TrustedAI internal CLI.

Global options (available on every command):
  --profile    Activate a named config profile
  --verbose    Enable verbose/debug output
  --json       Machine-readable JSON output (disables color/animation)
  --version    Show version and exit
"""

from __future__ import annotations

import importlib.metadata
import sys
from typing import Optional

import typer
from rich.console import Console

from tai.core.config import load_config
from tai.core.context import AppContext
from tai.core.errors import ConfigError

from tai.commands import secret, config, ai, api, claude, meetings, project, tasks
from tai.commands.auth import login, logout, whoami
from tai.docs import DOCS

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(
    name="tai",
    help="TrustedAI internal CLI — company AI tools, APIs, and secret management.",
    no_args_is_help=True,
    add_completion=True,          # generates shell completion scripts
    pretty_exceptions_enable=False,  # we handle errors ourselves
)


# ── Global options via callback ───────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p",
        help="Config profile to use (dev / staging / prod).",
        envvar="TAI_PROFILE",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output."),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (for scripting).",
        envvar="TAI_JSON",
    ),
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
    docs: bool = typer.Option(False, "--docs", help="Print LLM-friendly usage docs and exit."),
):
    if docs:
        print(DOCS)
        raise typer.Exit()

    if version:
        try:
            v = importlib.metadata.version("trusted-ai-cli")
        except importlib.metadata.PackageNotFoundError:
            v = "dev"
        console.print(f"tai {v}")
        raise typer.Exit()

    # Allow tests to inject a pre-built AppContext via ctx.obj
    if isinstance(ctx.obj, AppContext):
        if verbose:
            ctx.obj.verbose = verbose
        if json_output:
            ctx.obj.json_output = json_output
        return

    try:
        loaded_config = load_config(profile_override=profile)
    except ConfigError as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")
        if e.hint:
            err_console.print(f"[dim]Hint: {e.hint}[/dim]")
        raise typer.Exit(1)

    app_ctx = AppContext(
        profile=loaded_config.current_profile,
        verbose=verbose,
        json_output=json_output,
        config=loaded_config,
    )
    ctx.obj = app_ctx

    if verbose:
        err_console.print(f"[dim]Profile: {app_ctx.profile}[/dim]")


# ── Register built-in command groups ─────────────────────────────────────────

app.add_typer(secret.app)
app.add_typer(config.app)
app.add_typer(ai.app)
app.add_typer(api.app)
app.add_typer(claude.app)
app.add_typer(project.app)
app.add_typer(tasks.app)
app.add_typer(meetings.app)
app.command(name="link")(project.link)
app.command(name="unlink")(project.unlink)
app.command(name="open")(project.open_tool)
app.command(name="login")(login)
app.command(name="logout")(logout)
app.command(name="whoami")(whoami)


# ── Plugin discovery via entry points ─────────────────────────────────────────

def _load_plugins() -> None:
    """Auto-discover and register external plugin command groups."""
    try:
        eps = importlib.metadata.entry_points(group="tai.plugins")
    except Exception:
        return

    for ep in eps:
        try:
            plugin_app = ep.load()
            app.add_typer(plugin_app)
            if "--verbose" in sys.argv:
                err_console.print(f"[dim]Plugin loaded: {ep.name}[/dim]")
        except Exception as exc:
            err_console.print(f"[yellow]Warning:[/yellow] Failed to load plugin '{ep.name}': {exc}")


_load_plugins()
