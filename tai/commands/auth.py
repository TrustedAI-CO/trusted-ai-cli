"""tai auth — login, logout, whoami."""

import typer
from rich.console import Console

from tai.core import auth
from tai.core.context import get_ctx
from tai.core.errors import handle_error, TaiError

app = typer.Typer(name="auth", help="Authenticate with your company Google account.")
console = Console()
err_console = Console(stderr=True)


@app.command()
def login(ctx: typer.Context):
    """Sign in with your @company Google account (opens browser)."""
    app_ctx = get_ctx(ctx)
    profile_cfg = app_ctx.active_profile()
    if not profile_cfg.oauth_client_id:
        err_console.print("[bold red]Error:[/bold red] oauth_client_id not set in config.")
        err_console.print("[dim]Hint: Run: tai config set oauth_client_id <YOUR_CLIENT_ID>[/dim]")
        raise typer.Exit(1)

    console.print(f"Opening browser for {profile_cfg.company_domain} login…")
    try:
        email = auth.login(app_ctx.profile, profile_cfg.oauth_client_id, profile_cfg.company_domain, profile_cfg.oauth_client_secret)
        console.print(f"[green]✓[/green] Logged in as [bold]{email}[/bold]")
    except TaiError as e:
        handle_error(e)


@app.command()
def logout(ctx: typer.Context):
    """Sign out and revoke credentials."""
    app_ctx = get_ctx(ctx)
    try:
        auth.logout(app_ctx.profile)
        console.print("[green]✓[/green] Logged out.")
    except TaiError as e:
        handle_error(e)


@app.command()
def whoami(ctx: typer.Context):
    """Show the currently logged-in account."""
    import json
    app_ctx = get_ctx(ctx)
    email = auth.current_email(app_ctx.profile)
    if email:
        if app_ctx.json_output:
            console.print_json(json.dumps({"email": email, "profile": app_ctx.profile}))
        else:
            console.print(f"[bold]{email}[/bold]  (profile: {app_ctx.profile})")
    else:
        err_console.print("Not logged in.")
        err_console.print("[dim]Hint: Run: tai auth login[/dim]")
        raise typer.Exit(1)
