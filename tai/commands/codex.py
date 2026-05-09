"""tai codex — manage Codex CLI integration, skills, and agent instructions."""

from __future__ import annotations

import json
import shutil
from importlib.resources import files
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from tai.core.context import get_ctx
from tai.core.errors import ExitCode, SkillError, TaiError, handle_error
from tai.core.skills import SkillTarget, find_skill_source, install_skills, skills_install_dir

app = typer.Typer(name="codex", help="Manage Codex CLI integration, skills, and AGENTS.md guidance.")
console = Console()
err_console = Console(stderr=True)

MANAGED_AGENTS_MARKER = "tai:codex-agents-template"


def codex_home() -> Path:
    """Return the Codex configuration directory."""
    return Path.home() / ".codex"


def _installed_skill_count() -> int:
    base = skills_install_dir(SkillTarget.CODEX)
    if not base.is_dir():
        return 0
    return sum(
        1
        for child in base.iterdir()
        if child.is_dir()
        and child.name.startswith("tai-")
        and (child / "SKILL.md").is_file()
    )


def _template_text() -> str:
    try:
        return files("tai.data.codex").joinpath("AGENTS.md").read_text(encoding="utf-8")
    except (ModuleNotFoundError, FileNotFoundError):
        template = Path(__file__).resolve().parent.parent / "data" / "codex" / "AGENTS.md"
        return template.read_text(encoding="utf-8")


def _agents_path(path: Path | None) -> Path:
    base = (path or Path.cwd()).expanduser()
    if base.name == "AGENTS.md":
        return base
    return base / "AGENTS.md"


@app.command()
def status(ctx: typer.Context) -> None:
    """Show Codex CLI and tai asset installation status."""
    app_ctx = get_ctx(ctx)
    binary = shutil.which("codex")
    home = codex_home()
    skill_dir = skills_install_dir(SkillTarget.CODEX)
    agents = Path.cwd() / "AGENTS.md"
    data = {
        "installed": binary is not None,
        "binary": binary,
        "codex_home": str(home),
        "codex_home_exists": home.exists(),
        "skills_dir": str(skill_dir),
        "skills_installed": _installed_skill_count(),
        "agents_md": str(agents),
        "agents_md_exists": agents.exists(),
    }

    if app_ctx.json_output:
        console.print_json(json.dumps(data, indent=2))
        return

    table = Table(title="Codex Status")
    table.add_column("Item", style="cyan")
    table.add_column("Value")
    table.add_row("Binary", binary or "not found")
    table.add_row("Config", f"{home} ({'exists' if home.exists() else 'missing'})")
    table.add_row("Skills", f"{data['skills_installed']} tai skill(s) in {skill_dir}")
    table.add_row("AGENTS.md", f"{agents} ({'exists' if agents.exists() else 'missing'})")
    console.print(table)


@app.command("setup-skills")
def setup_skills(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Overwrite existing Codex skills."),
    json_flag: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Install or update bundled tai skills for Codex under ~/.codex/skills/."""
    app_ctx = get_ctx(ctx)
    use_json = app_ctx.json_output or json_flag

    try:
        source = find_skill_source()
        if source is None:
            raise SkillError(
                "Cannot find bundled skills",
                hint="Run from the project repo or install tai with pip.",
            )

        result = install_skills(source, force=force, target=SkillTarget.CODEX)
        install_path = skills_install_dir(SkillTarget.CODEX)

        if use_json:
            console.print_json(json.dumps({
                "installed": result.installed,
                "skipped": result.skipped,
                "install_path": str(install_path),
            }))
            return

        for name in result.installed:
            console.print(f"  [green]✓[/green] {name}")
        for name in result.skipped:
            console.print(f"  [dim]  {name}[/dim] (exists, use --force)")

        console.print(
            f"\n[green]{len(result.installed)} skill(s) installed[/green]"
            f", {len(result.skipped)} skipped — {install_path}"
        )
        console.print("[dim]Restart Codex to pick up new skills.[/dim]")

    except SkillError as exc:
        handle_error(exc)


@app.command("setup-agents")
def setup_agents(
    ctx: typer.Context,
    path: Path | None = typer.Option(None, "--path", "-p", help="Repository directory or AGENTS.md path."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing unmanaged AGENTS.md."),
    json_flag: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Create or refresh a tai-managed Codex AGENTS.md contributor guide."""
    app_ctx = get_ctx(ctx)
    use_json = app_ctx.json_output or json_flag
    agents_path = _agents_path(path)

    try:
        existed = agents_path.exists()
        if existed:
            existing = agents_path.read_text(encoding="utf-8")
            if MANAGED_AGENTS_MARKER not in existing and not force:
                err = TaiError(
                    f"AGENTS.md already exists and is not tai-managed: {agents_path}",
                    hint="Use --force to replace it, or edit the file manually.",
                )
                err.exit_code = ExitCode.CONFLICT
                raise err

        agents_path.parent.mkdir(parents=True, exist_ok=True)
        agents_path.write_text(_template_text(), encoding="utf-8")

        if use_json:
            console.print_json(json.dumps({
                "path": str(agents_path),
                "written": True,
                "overwritten": existed,
            }))
            return

        action = "Updated" if existed else "Installed"
        console.print(f"[green]{action}[/green] Codex AGENTS.md at {agents_path}")

    except TaiError as exc:
        handle_error(exc)
