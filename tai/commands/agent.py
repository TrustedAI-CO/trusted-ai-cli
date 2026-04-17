"""tai agent — spawn AI coding agents (Codex / Gemini CLI) as subprocesses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from tai.core.agent import (
    AgentBackend,
    AgentResult,
    AgentStatus,
    create_task,
    run_agent,
    run_parallel,
)
from tai.core.context import get_ctx
from tai.core.errors import TaiError, handle_error

app = typer.Typer(name="agent", help="Spawn AI coding agents (Codex / Gemini).")
console = Console()
err_console = Console(stderr=True)


def _backend_from_str(value: str) -> AgentBackend:
    try:
        return AgentBackend(value)
    except ValueError:
        raise typer.BadParameter(f"Unknown backend '{value}'. Use 'codex' or 'gemini'.")


def _print_results(results: list[AgentResult], *, json_output: bool) -> None:
    if json_output:
        rows = [
            {
                "id": r.id,
                "backend": r.backend.value,
                "status": r.status.value,
                "output": r.output,
                "duration_s": r.duration_s,
                "exit_code": r.exit_code,
            }
            for r in results
        ]
        console.print_json(json.dumps(rows, indent=2))
        return

    for r in results:
        icon = {"success": "[green]OK[/green]", "error": "[red]ERR[/red]", "timeout": "[yellow]TIMEOUT[/yellow]"}
        header = f"{icon[r.status.value]} [{r.backend.value}] {r.id}  ({r.duration_s}s)"
        console.print(header)
        console.print(r.output)
        console.print()


@app.command()
def run(
    ctx: typer.Context,
    prompt: str = typer.Argument(help="Task prompt for the agent."),
    backend: str = typer.Option("codex", "--backend", "-b", help="Backend: codex or gemini."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model override."),
    directory: Optional[str] = typer.Option(None, "--dir", "-d", help="Working directory."),
    timeout: float = typer.Option(300.0, "--timeout", "-t", help="Timeout in seconds."),
    sandbox: bool = typer.Option(False, "--sandbox", "-s", help="Sandbox mode (gemini)."),
) -> None:
    """Run a single AI coding agent."""
    app_ctx = get_ctx(ctx)
    try:
        task = create_task(
            prompt,
            backend=_backend_from_str(backend),
            working_dir=directory,
            model=model,
            timeout=timeout,
            sandbox=sandbox,
        )
        if app_ctx.verbose:
            err_console.print(f"[dim]Agent {task.id} ({task.backend.value}) starting...[/dim]")

        result = run_agent(task)
        _print_results([result], json_output=app_ctx.json_output)

        if result.status != AgentStatus.SUCCESS:
            raise typer.Exit(1)

    except FileNotFoundError as e:
        handle_error(TaiError(str(e)))


@app.command()
def parallel(
    ctx: typer.Context,
    file: Path = typer.Argument(help="JSON file with task definitions."),
    max_concurrent: int = typer.Option(5, "--max", help="Max concurrent agents."),
) -> None:
    """Run multiple agents in parallel from a JSON task file.

    File format (JSON array):
      [
        {"prompt": "fix the bug", "backend": "codex", "dir": "./src"},
        {"prompt": "add tests", "backend": "gemini", "model": "gemini-2.5-pro"}
      ]
    """
    app_ctx = get_ctx(ctx)
    try:
        if not file.exists():
            raise TaiError(f"File not found: {file}", hint="Provide a valid JSON task file.")

        entries = json.loads(file.read_text())
        if not isinstance(entries, list):
            raise TaiError("Task file must be a JSON array.")

        tasks = [
            create_task(
                entry["prompt"],
                backend=_backend_from_str(entry.get("backend", "codex")),
                working_dir=entry.get("dir"),
                model=entry.get("model"),
                timeout=entry.get("timeout", 300.0),
                sandbox=entry.get("sandbox", False),
            )
            for entry in entries
        ]

        if app_ctx.verbose:
            err_console.print(f"[dim]Launching {len(tasks)} agents (max {max_concurrent} concurrent)...[/dim]")

        results = run_parallel(tasks, max_concurrent=max_concurrent)
        _print_results(results, json_output=app_ctx.json_output)

        failed = sum(1 for r in results if r.status != AgentStatus.SUCCESS)
        if failed:
            raise typer.Exit(1)

    except (FileNotFoundError, json.JSONDecodeError) as e:
        handle_error(TaiError(str(e)))


@app.command()
def backends(ctx: typer.Context) -> None:
    """List available agent backends and their status."""
    import shutil

    app_ctx = get_ctx(ctx)

    rows = []
    for b in AgentBackend:
        installed = shutil.which(b.value) is not None
        path = shutil.which(b.value) or ""
        rows.append({"backend": b.value, "installed": installed, "path": path})

    if app_ctx.json_output:
        console.print_json(json.dumps(rows, indent=2))
        return

    table = Table(title="Agent Backends")
    table.add_column("Backend", style="cyan")
    table.add_column("Status")
    table.add_column("Path", style="dim")

    for row in rows:
        status = "[green]installed[/green]" if row["installed"] else "[red]not found[/red]"
        table.add_row(row["backend"], status, row["path"])

    console.print(table)
