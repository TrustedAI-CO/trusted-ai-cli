"""tai skills — install and update Claude Code skills."""

import json

import typer
from rich.console import Console

from tai.core.context import get_ctx
from tai.core.errors import SkillError, handle_error
from tai.core.skills import (
    SKILL_PREFIX,
    discover_skills,
    find_skill_source,
    install_skills,
    installed_version,
    is_installed,
    skills_install_dir,
    InstallResult,
)

app = typer.Typer(name="skills", help="Manage Claude Code skills for your team.")
console = Console()
err_console = Console(stderr=True)


@app.command("setup")
def setup(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Overwrite existing skills."),
    json_flag: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Install bundled Claude Code skills as tai-* personal skills."""
    app_ctx = get_ctx(ctx)
    use_json = app_ctx.json_output or json_flag

    try:
        source = find_skill_source()
        if source is None:
            raise SkillError(
                "Cannot find bundled skills",
                hint="Run from the project repo or install tai with pip.",
            )

        result = install_skills(source, force=force)

        if use_json:
            console.print_json(json.dumps({
                "installed": result.installed,
                "skipped": result.skipped,
                "install_path": str(skills_install_dir()),
            }))
            return

        for name in result.installed:
            console.print(f"  [green]✓[/green] {name}")
        for name in result.skipped:
            console.print(f"  [dim]  {name}[/dim] (exists, use --force to overwrite)")

        console.print(
            f"\n[green]{len(result.installed)} skill(s) installed[/green]"
            f", {len(result.skipped)} skipped"
            f" — {skills_install_dir()}"
        )
        console.print("[dim]Restart Claude Code to pick up new skills.[/dim]")

    except SkillError as exc:
        handle_error(exc)


@app.command("update")
def update(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Update installed skills to the latest bundled version."""
    app_ctx = get_ctx(ctx)
    use_json = app_ctx.json_output or json_flag

    try:
        source = find_skill_source()
        if source is None:
            raise SkillError(
                "Cannot find bundled skills",
                hint="Run from the project repo or install tai with pip.",
            )

        if not is_installed():
            raise SkillError(
                "No tai skills installed yet",
                hint="Run: tai skills setup",
            )

        bundled = discover_skills(source)
        updated: list[str] = []
        already_current: list[str] = []
        newly_installed: list[str] = []

        for skill in bundled:
            current = installed_version(skill.name)
            if current is None:
                newly_installed.append(skill.name)
            elif current != skill.version:
                updated.append(skill.name)
            else:
                already_current.append(skill.name)

        install_skills(source, force=True)

        if use_json:
            console.print_json(json.dumps({
                "updated": updated,
                "newly_installed": newly_installed,
                "already_current": already_current,
            }))
            return

        prefix = f"{SKILL_PREFIX}-"
        for name in newly_installed:
            console.print(f"  [green]+ {prefix}{name}[/green] (new)")
        for name in updated:
            console.print(f"  [green]↑ {prefix}{name}[/green] (updated)")
        for name in already_current:
            console.print(f"  [dim]  {prefix}{name}[/dim] (current)")

        total_changed = len(newly_installed) + len(updated)
        if total_changed:
            console.print(f"\n[green]{total_changed} skill(s) updated[/green]")
            console.print("[dim]Restart Claude Code to pick up changes.[/dim]")
        else:
            console.print("\n[dim]All skills are up to date.[/dim]")

    except SkillError as exc:
        handle_error(exc)
