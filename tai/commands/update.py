"""tai update — self-update the CLI from GitHub Releases."""

from __future__ import annotations

import json
import shutil

import typer
from rich.console import Console

from tai.core.context import get_ctx
from tai.core.updater import (
    UpdateCheck,
    UpdateError,
    check_update,
    clear_update_cache,
    detect_installer,
    download_wheel,
    install_wheel,
    run_post_update,
    save_update_cache,
)

console = Console()
err_console = Console(stderr=True)


def update(
    ctx: typer.Context,
    check: bool = typer.Option(False, "--check", "-c", help="Check for updates without installing."),
) -> None:
    """Update tai to the latest version from GitHub Releases."""
    app_ctx = get_ctx(ctx)
    use_json = app_ctx.json_output

    try:
        info = check_update()
    except UpdateError as exc:
        _print_error(exc, use_json)
        raise typer.Exit(1)

    save_update_cache(info)

    if check:
        _print_check_result(info, use_json)
        return

    if not info.update_available:
        _print_up_to_date(info, use_json)
        return

    _run_update(info, use_json)


def _print_check_result(info: UpdateCheck, use_json: bool) -> None:
    if use_json:
        console.print_json(json.dumps({
            "current": info.current,
            "latest": info.latest,
            "update_available": info.update_available,
        }))
        return

    if info.update_available:
        console.print(
            f"Update available: [bold]{info.current}[/bold] -> [bold green]{info.latest}[/bold green]\n"
            "Run [cyan]tai update[/cyan] to install."
        )
    else:
        console.print(f"Already up to date: [bold]{info.current}[/bold]")


def _print_up_to_date(info: UpdateCheck, use_json: bool) -> None:
    if use_json:
        console.print_json(json.dumps({
            "current": info.current,
            "latest": info.latest,
            "updated": False,
        }))
        return

    console.print(f"Already up to date: [bold]{info.current}[/bold]")


def _run_update(info: UpdateCheck, use_json: bool) -> None:
    release = info.release
    installer = detect_installer()

    if not use_json:
        console.print(
            f"Updating [bold]{info.current}[/bold] -> [bold green]{info.latest}[/bold green] "
            f"via {installer.value}..."
        )

    try:
        wheel_path = download_wheel(release.asset)
    except UpdateError as exc:
        _print_error(exc, use_json)
        raise typer.Exit(1)

    try:
        install_wheel(wheel_path, installer)
    except UpdateError as exc:
        _print_error(exc, use_json)
        raise typer.Exit(1)
    finally:
        # Clean up temp directory
        shutil.rmtree(wheel_path.parent, ignore_errors=True)

    clear_update_cache()

    if not use_json:
        console.print(f"[green]Updated to {info.latest}[/green]")
        console.print("\nRefreshing skills, hooks, and templates...")

    skills_ok, hooks_ok, templates_ok = run_post_update()

    if not use_json:
        _print_post_update(skills_ok, hooks_ok, templates_ok)
    else:
        console.print_json(json.dumps({
            "current": info.current,
            "latest": info.latest,
            "updated": True,
            "skills_refreshed": skills_ok,
            "hooks_refreshed": hooks_ok,
            "templates_refreshed": templates_ok,
        }))


def _print_post_update(skills_ok: bool, hooks_ok: bool, templates_ok: bool) -> None:
    if skills_ok:
        console.print("  [green]Skills refreshed[/green]")
    else:
        err_console.print("  [yellow]Warning: skills refresh failed. Run 'tai claude setup-skills' manually.[/yellow]")

    if hooks_ok:
        console.print("  [green]Hooks refreshed[/green]")
    else:
        err_console.print("  [yellow]Warning: hooks refresh failed. Run 'tai claude setup-hooks' manually.[/yellow]")

    if templates_ok:
        console.print("  [green]Templates refreshed[/green]")
    else:
        err_console.print("  [yellow]Warning: templates refresh failed. Run 'tai pdf setup-templates' manually.[/yellow]")


def _print_error(exc: UpdateError, use_json: bool) -> None:
    if use_json:
        console.print_json(json.dumps({"error": str(exc)}))
        return

    err_console.print(f"[bold red]Error:[/bold red] {exc}")
    if exc.hint:
        err_console.print(f"[dim]Hint: {exc.hint}[/dim]")
