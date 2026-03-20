"""tai setup — interactive config wizard that prompts for every config variable."""

from __future__ import annotations

import typer
from rich.console import Console

from tai.core.config import ProfileConfig, load_config, save_config
from tai.core.context import get_ctx
from tai.core.prompt import is_interactive
from tai.core.updater import run_post_update

console = Console()
err_console = Console(stderr=True)

_SENSITIVE_KEYWORDS = frozenset({"secret", "password", "token"})


def _is_sensitive(field_name: str) -> bool:
    lower = field_name.lower()
    return any(kw in lower for kw in _SENSITIVE_KEYWORDS)


def _mask(value: str) -> str:
    if not value:
        return "(empty)"
    return value[:4] + "****" if len(value) > 4 else "****"


def setup(ctx: typer.Context) -> None:
    """Interactive setup — prompts for every config variable, skip with Enter."""
    if not is_interactive():
        err_console.print(
            "[bold red]Error:[/bold red] tai setup requires an interactive terminal.\n"
            "[dim]Hint: Use `tai config set <key> <value>` instead.[/dim]"
        )
        raise typer.Exit(1)

    app_ctx = get_ctx(ctx)
    config = load_config()
    profile_name = app_ctx.profile
    profile = config.profiles.get(profile_name, ProfileConfig())
    current_values = profile.model_dump()

    console.print(f"\n[bold]tai setup[/bold] — profile: [cyan]{profile_name}[/cyan]")
    console.print("Press [bold]Enter[/bold] to keep current value, or type a new one.\n")

    updates: dict[str, object] = {}

    for field_name, field_info in ProfileConfig.model_fields.items():
        current = current_values.get(field_name, field_info.default)
        sensitive = _is_sensitive(field_name)
        display_value = _mask(str(current)) if sensitive else str(current)

        console.print(f"  [bold cyan]{field_name}[/bold cyan] [dim](current: {display_value})[/dim]")

        raw = typer.prompt(
            f"  {field_name}",
            default="",
            show_default=False,
            hide_input=sensitive,
        )
        raw = raw.strip()

        if not raw:
            continue

        coerced = _coerce(raw, type(current))
        updates[field_name] = coerced
        console.print(f"    [green]-> {field_name} updated[/green]")

    if not updates:
        console.print("\n[dim]No changes made.[/dim]")
        return

    updated_profile = profile.model_copy(update=updates)
    config.profiles[profile_name] = updated_profile
    save_config(config)

    console.print(f"\n[green]Saved {len(updates)} change(s) to profile [bold]{profile_name}[/bold].[/green]")

    console.print("\nInstalling skills, hooks, and templates...")
    skills_ok, hooks_ok, templates_ok = run_post_update()

    if skills_ok:
        console.print("  [green]Skills installed[/green]")
    else:
        err_console.print("  [yellow]Warning: skills install failed. Run 'tai claude setup-skills' manually.[/yellow]")

    if hooks_ok:
        console.print("  [green]Hooks installed[/green]")
    else:
        err_console.print("  [yellow]Warning: hooks install failed. Run 'tai claude setup-hooks' manually.[/yellow]")

    if templates_ok:
        console.print("  [green]Templates installed[/green]")
    else:
        err_console.print("  [yellow]Warning: templates install failed. Run 'tai pdf setup-templates' manually.[/yellow]")


def _coerce(raw: str, target_type: type) -> object:
    if target_type is int:
        return int(raw)
    if target_type is float:
        return float(raw)
    if target_type is bool:
        return raw.lower() in ("true", "1", "yes")
    return raw
