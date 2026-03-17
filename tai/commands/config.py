"""tai config — get, set, list, list-profiles, switch-profile."""

import json

import typer
from rich.console import Console
from rich.table import Table

from tai.core.config import load_config, save_config, ProfileConfig
from tai.core.context import get_ctx
from tai.core.errors import handle_error, TaiError, ConfigError

app = typer.Typer(name="config", help="Manage CLI configuration and profiles.")
console = Console()
err_console = Console(stderr=True)


@app.command("get")
def get_value(
    ctx: typer.Context,
    key: str = typer.Argument(help="Config key (e.g. api_base_url)"),
):
    """Print a config value for the active profile."""
    app_ctx = get_ctx(ctx)
    profile_cfg = app_ctx.active_profile()
    value = getattr(profile_cfg, key, None)
    if value is None:
        err_console.print(f"Unknown config key: [bold]{key}[/bold]")
        raise typer.Exit(1)

    if app_ctx.json_output:
        console.print_json(json.dumps({"key": key, "value": value, "profile": app_ctx.profile}))
    else:
        console.print(value)


@app.command("set")
def set_value(
    ctx: typer.Context,
    key: str = typer.Argument(help="Config key"),
    value: str = typer.Argument(help="New value"),
):
    """Set a config value in the active profile."""
    app_ctx = get_ctx(ctx)
    config = load_config()
    profile_name = app_ctx.profile
    profile = config.profiles.get(profile_name, ProfileConfig())

    if not hasattr(profile, key):
        err_console.print(f"Unknown config key: [bold]{key}[/bold]")
        raise typer.Exit(1)

    updated = profile.model_copy(update={key: value})
    config.profiles[profile_name] = updated
    save_config(config)
    console.print(f"[green]✓[/green] {key} = {value}  (profile: {profile_name})")


@app.command("list")
def list_values(ctx: typer.Context):
    """List all config values for the active profile."""
    app_ctx = get_ctx(ctx)
    profile_cfg = app_ctx.active_profile()
    data = profile_cfg.model_dump()

    if app_ctx.json_output:
        console.print_json(json.dumps({"profile": app_ctx.profile, "config": data}))
        return

    table = Table(title=f"Config — profile: {app_ctx.profile}")
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    for k, v in data.items():
        table.add_row(k, str(v))
    console.print(table)


@app.command("list-profiles")
def list_profiles(ctx: typer.Context):
    """List all available profiles."""
    app_ctx = get_ctx(ctx)
    config = load_config()
    profiles = list(config.profiles.keys())

    if app_ctx.json_output:
        console.print_json(json.dumps({"current": config.current_profile, "profiles": profiles}))
        return

    for name in profiles:
        marker = " [green]← active[/green]" if name == config.current_profile else ""
        console.print(f"  {name}{marker}")


@app.command("switch-profile")
def switch_profile(
    ctx: typer.Context,
    profile: str = typer.Argument(help="Profile name to activate"),
):
    """Switch the active profile (dev / staging / prod)."""
    try:
        config = load_config()
        if profile not in config.profiles:
            raise ConfigError(f"Profile '{profile}' not found", hint="Run: tai config list-profiles")
        config.current_profile = profile
        save_config(config)
        console.print(f"[green]✓[/green] Switched to profile [bold]{profile}[/bold]")
    except TaiError as e:
        handle_error(e)
