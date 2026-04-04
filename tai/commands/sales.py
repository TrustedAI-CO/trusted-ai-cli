"""tai sales — manage sales pipelines on Hnavi and Aimitsu."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from tai.core.errors import ExitCode

app = typer.Typer(name="sales", help="Manage sales pipelines on Hnavi and Aimitsu.")
hnavi_app = typer.Typer(name="hnavi", help="発注ナビ (Hnavi) operations.")
aimitsu_app = typer.Typer(name="aimitsu", help="アイミツ (Aimitsu) operations.")

app.add_typer(hnavi_app)
app.add_typer(aimitsu_app)

console = Console()
err_console = Console(stderr=True)


def _check_playwright() -> None:
    """Check if playwright is installed."""
    try:
        import playwright  # noqa: F401
    except ImportError:
        err_console.print(
            "[bold red]Error:[/bold red] Playwright is not installed.\n"
            "[dim]Install with: pip install 'trusted-ai-cli[sales]' && playwright install chromium[/dim]"
        )
        raise typer.Exit(ExitCode.ERROR)


# ══════════════════════════════════════════════════════════════════════════════
# Top-level sales commands
# ══════════════════════════════════════════════════════════════════════════════


@app.command("status")
def sales_status(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show summary status for all sales platforms."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, HnaviClient, AimitsuClient

    results = {"hnavi": {}, "aimitsu": {}}

    with SalesBrowser() as browser:
        # Hnavi summary
        try:
            hnavi = HnaviClient(browser)
            jobs = hnavi.list_jobs()
            negotiations = hnavi.list_negotiations()
            results["hnavi"] = {
                "jobs": len(jobs),
                "negotiations": len(negotiations),
                "status": "ok",
            }
        except Exception as e:
            results["hnavi"] = {"status": "error", "error": str(e)}

        # Aimitsu summary
        try:
            aimitsu = AimitsuClient(browser)
            projects = aimitsu.list_projects()
            results["aimitsu"] = {
                "projects": len(projects),
                "status": "ok",
            }
        except Exception as e:
            results["aimitsu"] = {"status": "error", "error": str(e)}

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    if json_output:
        console.print_json(json.dumps(results))
    else:
        console.print("\n[bold]Sales Pipeline Status[/bold]\n")

        # Hnavi
        if results["hnavi"].get("status") == "ok":
            console.print(f"[cyan]Hnavi (発注ナビ)[/cyan]")
            console.print(f"  Jobs with AI tag: {results['hnavi']['jobs']}")
            console.print(f"  Active negotiations: {results['hnavi']['negotiations']}")
        else:
            console.print(f"[cyan]Hnavi[/cyan]: [red]Error[/red] - {results['hnavi'].get('error')}")

        console.print()

        # Aimitsu
        if results["aimitsu"].get("status") == "ok":
            console.print(f"[cyan]Aimitsu (アイミツ)[/cyan]")
            console.print(f"  Active projects: {results['aimitsu']['projects']}")
        else:
            console.print(f"[cyan]Aimitsu[/cyan]: [red]Error[/red] - {results['aimitsu'].get('error')}")


@app.command("login")
def sales_login(
    ctx: typer.Context,
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
) -> None:
    """Test login to all sales platforms."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, HnaviClient, AimitsuClient

    with SalesBrowser(headless=not visible) as browser:
        # Test Hnavi
        console.print("[cyan]Testing Hnavi login...[/cyan]", end=" ")
        try:
            hnavi = HnaviClient(browser)
            hnavi.login()
            console.print("[green]OK[/green]")
        except Exception as e:
            console.print(f"[red]Failed[/red]: {e}")

        # Test Aimitsu
        console.print("[cyan]Testing Aimitsu login...[/cyan]", end=" ")
        try:
            aimitsu = AimitsuClient(browser)
            aimitsu.login()
            console.print("[green]OK[/green]")
        except Exception as e:
            console.print(f"[red]Failed[/red]: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Hnavi commands
# ══════════════════════════════════════════════════════════════════════════════


@hnavi_app.callback(invoke_without_command=True)
def hnavi_status(ctx: typer.Context) -> None:
    """Show Hnavi summary (jobs + negotiations count)."""
    if ctx.invoked_subcommand is not None:
        return

    _check_playwright()

    from tai.core.sales import SalesBrowser, HnaviClient

    with SalesBrowser() as browser:
        client = HnaviClient(browser)
        jobs = client.list_jobs()
        negotiations = client.list_negotiations()

    console.print(f"\n[bold cyan]Hnavi (発注ナビ)[/bold cyan]")
    console.print(f"  AI Jobs available: {len(jobs)}")
    console.print(f"  Active negotiations: {len(negotiations)}\n")


@hnavi_app.command("jobs")
def hnavi_jobs(
    ctx: typer.Context,
    job_id: Annotated[str | None, typer.Argument(help="Job ID for details (omit to list all).")] = None,
    tag: str = typer.Option("AI", "--tag", "-t", help="Filter by tag."),
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List AI jobs or show job details."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, HnaviClient

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    with SalesBrowser(headless=not visible) as browser:
        client = HnaviClient(browser)

        if job_id:
            # Show job details
            job = client.get_job(job_id)

            if json_output:
                console.print_json(json.dumps(job))
            else:
                console.print(f"\n[bold]{job.get('title', 'Job ' + job_id)}[/bold]")
                console.print(f"[dim]URL: {job.get('url')}[/dim]\n")
                if job.get("description"):
                    console.print(job["description"][:2000])  # Truncate long descriptions
        else:
            # List jobs
            jobs = client.list_jobs(tag_filter=tag)

            if json_output:
                console.print_json(json.dumps([j.to_dict() for j in jobs]))
            elif not jobs:
                console.print(f"[dim]No jobs found with tag '{tag}'.[/dim]")
            else:
                table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
                table.add_column("ID", style="dim", no_wrap=True)
                table.add_column("Title")
                table.add_column("Budget", style="dim")
                table.add_column("Tags", style="cyan")

                for job in jobs:
                    table.add_row(
                        job.id,
                        job.title[:50],
                        job.budget or "—",
                        ", ".join(job.tags or []),
                    )

                console.print(table)


@hnavi_app.command("active")
def hnavi_active(
    ctx: typer.Context,
    neg_id: Annotated[str | None, typer.Argument(help="Negotiation ID for details (omit to list all).")] = None,
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List active negotiations or show negotiation details."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, HnaviClient

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    with SalesBrowser(headless=not visible) as browser:
        client = HnaviClient(browser)

        if neg_id:
            # Show negotiation details
            neg = client.get_negotiation(neg_id)

            if json_output:
                console.print_json(json.dumps(neg))
            else:
                console.print(f"\n[bold]{neg.get('title', 'Negotiation ' + neg_id)}[/bold]")
                if neg.get("company"):
                    console.print(f"Company: {neg['company']}")
                console.print(f"[dim]URL: {neg.get('url')}[/dim]\n")

                # Show messages
                messages = neg.get("messages", [])
                if messages:
                    console.print("[bold]Messages:[/bold]\n")
                    for msg in messages:
                        console.print(f"[cyan]{msg['sender']}[/cyan] ({msg.get('date', '—')})")
                        console.print(f"  {msg['content']}\n")
                else:
                    console.print("[dim]No messages found.[/dim]")
        else:
            # List negotiations
            negotiations = client.list_negotiations()

            if json_output:
                console.print_json(json.dumps([n.to_dict() for n in negotiations]))
            elif not negotiations:
                console.print("[dim]No active negotiations.[/dim]")
            else:
                table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
                table.add_column("ID", style="dim", no_wrap=True)
                table.add_column("Title")
                table.add_column("Company", style="dim")
                table.add_column("Status", style="cyan")
                table.add_column("Last Message", style="dim")

                for neg in negotiations:
                    table.add_row(
                        neg.id,
                        neg.title[:40],
                        neg.company or "—",
                        neg.status or "—",
                        neg.last_message_date or "—",
                    )

                console.print(table)


@hnavi_app.command("send")
def hnavi_send(
    ctx: typer.Context,
    neg_id: Annotated[str, typer.Argument(help="Negotiation ID.")],
    message: Annotated[str, typer.Argument(help="Message to send.")],
    file: Path | None = typer.Option(None, "--file", "-f", help="File to attach."),
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
) -> None:
    """Send a message to a negotiation."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, HnaviClient

    if file and not file.exists():
        err_console.print(f"[bold red]Error:[/bold red] File not found: {file}")
        raise typer.Exit(ExitCode.NOT_FOUND)

    with SalesBrowser(headless=not visible) as browser:
        client = HnaviClient(browser)
        try:
            client.send_message(neg_id, message, str(file) if file else None)
            console.print(f"[green]Message sent[/green] to negotiation {neg_id}")
        except Exception as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(ExitCode.ERROR)


# ══════════════════════════════════════════════════════════════════════════════
# Aimitsu commands
# ══════════════════════════════════════════════════════════════════════════════


@aimitsu_app.callback(invoke_without_command=True)
def aimitsu_status(ctx: typer.Context) -> None:
    """Show Aimitsu summary (project count)."""
    if ctx.invoked_subcommand is not None:
        return

    _check_playwright()

    from tai.core.sales import SalesBrowser, AimitsuClient

    with SalesBrowser() as browser:
        client = AimitsuClient(browser)
        projects = client.list_projects()

    console.print(f"\n[bold cyan]Aimitsu (アイミツ)[/bold cyan]")
    console.print(f"  Active projects: {len(projects)}\n")


@aimitsu_app.command("list")
def aimitsu_list(
    ctx: typer.Context,
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List projects in negotiation."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, AimitsuClient

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    with SalesBrowser(headless=not visible) as browser:
        client = AimitsuClient(browser)
        projects = client.list_projects()

    if json_output:
        console.print_json(json.dumps([p.to_dict() for p in projects]))
    elif not projects:
        console.print("[dim]No active projects.[/dim]")
    else:
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("No.", style="dim", no_wrap=True)
        table.add_column("Title")
        table.add_column("Customer", style="dim")
        table.add_column("Status", style="cyan")

        for proj in projects:
            table.add_row(
                proj.no,
                proj.title[:50],
                proj.customer or "—",
                proj.status or "—",
            )

        console.print(table)


@aimitsu_app.command("show")
def aimitsu_show(
    ctx: typer.Context,
    project_no: Annotated[str, typer.Argument(help="Project number (案件No.).")],
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show project details."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, AimitsuClient

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    with SalesBrowser(headless=not visible) as browser:
        client = AimitsuClient(browser)
        project = client.get_project(project_no)

    if json_output:
        console.print_json(json.dumps(project))
    else:
        console.print(f"\n[bold]{project.get('title', 'Project ' + project_no)}[/bold]")
        if project.get("customer"):
            console.print(f"Customer: {project['customer']}")
        console.print(f"[dim]URL: {project.get('url')}[/dim]\n")

        # Show description
        if project.get("description"):
            console.print(project["description"][:2000])

        # Show messages
        messages = project.get("messages", [])
        if messages:
            console.print("\n[bold]Messages:[/bold]\n")
            for msg in messages:
                console.print(f"[cyan]{msg['sender']}[/cyan] ({msg.get('date', '—')})")
                console.print(f"  {msg['content']}\n")


@aimitsu_app.command("send")
def aimitsu_send(
    ctx: typer.Context,
    project_no: Annotated[str, typer.Argument(help="Project number (案件No.).")],
    message: Annotated[str, typer.Argument(help="Message to send.")],
    file: Path | None = typer.Option(None, "--file", "-f", help="File to attach."),
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
) -> None:
    """Send a message to a project."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, AimitsuClient

    if file and not file.exists():
        err_console.print(f"[bold red]Error:[/bold red] File not found: {file}")
        raise typer.Exit(ExitCode.NOT_FOUND)

    with SalesBrowser(headless=not visible) as browser:
        client = AimitsuClient(browser)
        try:
            client.send_message(project_no, message, str(file) if file else None)
            console.print(f"[green]Message sent[/green] to project {project_no}")
        except Exception as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(ExitCode.ERROR)
