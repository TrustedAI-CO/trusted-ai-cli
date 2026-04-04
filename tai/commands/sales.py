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
            console.print(f"  Jobs available: {results['hnavi']['jobs']}")
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
    console.print(f"  Jobs available: {len(jobs)}")
    console.print(f"  Active negotiations: {len(negotiations)}\n")


@hnavi_app.command("jobs")
def hnavi_jobs(
    ctx: typer.Context,
    job_id: Annotated[str | None, typer.Argument(help="Job ID for details (omit to list all).")] = None,
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category (e.g., AI, システム, ホームページ)."),
    saas: bool = typer.Option(False, "--saas", help="Include SaaS tab jobs."),
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List jobs or show job details."""
    _check_playwright()

    from tai.core.sales import SalesBrowser, HnaviClient

    json_output = json_flag or getattr(ctx.obj, "json_output", False)

    with SalesBrowser(headless=not visible) as browser:
        client = HnaviClient(browser)

        if job_id:
            # Show job details
            # If job_id looks like a display No. (12 digits), find the URL ID first
            if len(job_id) == 12 and job_id.isdigit():
                # Search for the job to get URL ID
                all_jobs = client.list_jobs(include_saas=True)
                url_id = None
                for j in all_jobs:
                    if j.id == job_id:
                        url_id = j.url.split("/")[-1]
                        break
                if not url_id:
                    err_console.print(f"[bold red]Error:[/bold red] Job No. {job_id} not found")
                    raise typer.Exit(ExitCode.NOT_FOUND)
                job = client.get_job(url_id)
            else:
                job = client.get_job(job_id)

            if json_output:
                console.print_json(json.dumps(job))
            else:
                # Header
                console.print(f"\n[bold]{job.get('title', 'Job ' + job_id)}[/bold]")
                console.print(f"[dim]No. {job.get('no', job_id)} | {job.get('url')}[/dim]\n")

                # Status line
                status_parts = []
                if job.get("status"):
                    status_parts.append(f"[red]{job['status']}[/red]")
                if job.get("deadline"):
                    status_parts.append(f"〆 {job['deadline']}")
                if job.get("category"):
                    status_parts.append(f"[cyan]{job['category']}[/cyan]")
                if status_parts:
                    console.print(" | ".join(status_parts))

                # Company info
                info_parts = []
                if job.get("max_companies"):
                    info_parts.append(f"上限: {job['max_companies']}")
                if job.get("company_size"):
                    info_parts.append(f"規模: {job['company_size']}")
                if job.get("company_location"):
                    info_parts.append(f"拠点: {job['company_location']}")
                if job.get("has_website"):
                    info_parts.append(f"HP: {job['has_website']}")
                if info_parts:
                    console.print(" | ".join(info_parts))

                # Entry conditions
                if job.get("entry_conditions"):
                    console.print("\n[bold]エントリー条件[/bold]")
                    for i, cond in enumerate(job["entry_conditions"], 1):
                        console.print(f"  {i}. {cond}")

                # Inquiry content
                if job.get("inquiry_content"):
                    console.print(f"\n[bold]お問い合わせ内容[/bold]")
                    console.print(f"  {job['inquiry_content']}")

                # Hearing content
                if job.get("hearing_content"):
                    console.print(f"\n[bold]ヒアリング内容[/bold]")
                    # Indent each line
                    for line in job["hearing_content"].split("\n"):
                        console.print(f"  {line}")
        else:
            # List jobs
            jobs = client.list_jobs(category=category, include_saas=saas)

            if json_output:
                console.print_json(json.dumps([j.to_dict() for j in jobs]))
            elif not jobs:
                if category:
                    console.print(f"[dim]No jobs found with category '{category}'.[/dim]")
                else:
                    console.print("[dim]No jobs found.[/dim]")
            else:
                table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
                table.add_column("No.", style="dim", no_wrap=True)
                table.add_column("Title")
                table.add_column("Deadline", style="dim")
                table.add_column("Category", style="cyan")

                for job in jobs:
                    table.add_row(
                        job.id,
                        job.title[:50],
                        job.deadline or "—",
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


@hnavi_app.command("entry")
def hnavi_entry(
    ctx: typer.Context,
    job_id: Annotated[str, typer.Argument(help="Job ID to enter (URL ID or display No.).")],
    visible: bool = typer.Option(False, "--visible", help="Show browser window."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Submit an entry for a job (interactive)."""
    _check_playwright()

    import sys
    from tai.core.sales import SalesBrowser, HnaviClient

    # Check if running in interactive mode
    if not sys.stdin.isatty():
        err_console.print(
            "[bold red]Error:[/bold red] Entry command requires interactive mode.\n"
            "[dim]Run in a terminal or use the API directly.[/dim]"
        )
        raise typer.Exit(ExitCode.USAGE)

    with SalesBrowser(headless=not visible) as browser:
        client = HnaviClient(browser)

        # If job_id looks like a display No. (12 digits), find the URL ID first
        url_id = job_id
        if len(job_id) == 12 and job_id.isdigit():
            console.print(f"[dim]Looking up job No. {job_id}...[/dim]")
            all_jobs = client.list_jobs(include_saas=True)
            for j in all_jobs:
                if j.id == job_id:
                    url_id = j.url.split("/")[-1]
                    break
            else:
                err_console.print(f"[bold red]Error:[/bold red] Job No. {job_id} not found")
                raise typer.Exit(ExitCode.NOT_FOUND)

        # Get entry form
        try:
            console.print(f"[dim]Loading entry form...[/dim]")
            form = client.get_entry_form(url_id)
        except RuntimeError as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(ExitCode.ERROR)

        console.print(f"\n[bold]Entry for: {form.job_title}[/bold]\n")

        # Collect answers to questions
        answers: list[str] = []
        console.print("[bold cyan]エントリー条件への回答[/bold cyan]")
        console.print("[dim]各条件に対する回答を入力してください。[/dim]\n")

        for q in form.questions:
            console.print(f"[bold]{q.index + 1}. {q.question}[/bold]")
            if q.required:
                console.print("[dim](必須)[/dim]")
            answer = typer.prompt("回答", default="")
            answers.append(answer)
            console.print()

        # Self introduction
        console.print("[bold cyan]自己推薦文[/bold cyan]")
        console.print("[dim]御社をお勧めする理由や実績を記入してください。[/dim]")
        self_intro = typer.prompt("自己推薦文", default="")
        console.print()

        # Team member selection
        console.print("[bold cyan]担当者選択[/bold cyan]")
        console.print("[dim]担当者を選択してください (カンマ区切りで番号を入力、例: 1,3)[/dim]\n")

        for i, member in enumerate(form.team_members, 1):
            selected_mark = "✓" if member.selected else " "
            console.print(f"  [{selected_mark}] {i}. {member.name}")

        # Get default selection (pre-selected members)
        default_selection = ",".join(
            str(i + 1)
            for i, m in enumerate(form.team_members)
            if m.selected
        ) or "1"

        member_input = typer.prompt("担当者番号", default=default_selection)
        selected_member_ids: list[str] = []
        try:
            indices = [int(x.strip()) - 1 for x in member_input.split(",") if x.strip()]
            for idx in indices:
                if 0 <= idx < len(form.team_members):
                    selected_member_ids.append(form.team_members[idx].id)
        except ValueError:
            pass

        if not selected_member_ids:
            # Default to first member
            if form.team_members:
                selected_member_ids = [form.team_members[0].id]

        console.print()

        # Confirmation
        console.print("[bold]確認[/bold]")
        console.print(f"  案件: {form.job_title}")
        console.print(f"  回答数: {len([a for a in answers if a])}")
        console.print(f"  担当者: {len(selected_member_ids)}名")
        console.print()

        if not yes:
            confirm = typer.confirm("エントリーを送信しますか?", default=True)
            if not confirm:
                console.print("[yellow]キャンセルしました。[/yellow]")
                raise typer.Exit(0)

        # Submit entry
        try:
            console.print("[dim]Submitting entry...[/dim]")
            client.submit_entry(
                job_id=url_id,
                answers=answers,
                self_introduction=self_intro,
                team_member_ids=selected_member_ids,
            )
            console.print(f"\n[bold green]✓ エントリーを送信しました![/bold green]")
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
        # Header with title and customer
        title = project.get("title", "")
        customer = project.get("customer", "Unknown")
        console.print(f"\n[bold]{title or customer}[/bold]")
        if title and customer:
            console.print(f"カスタマー: {customer}")
        console.print(f"[dim]URL: {project.get('url')}[/dim]")

        # Project metadata
        if project.get("inquiry_no"):
            console.print(f"お問い合わせNo.: {project['inquiry_no']}")
        if project.get("request_date"):
            console.print(f"依頼日: {project['request_date']}")

        # Project background and details
        if project.get("background"):
            console.print("\n[bold cyan]発注の背景[/bold cyan]")
            console.print(f"  {project['background']}")

        # Show individual detail fields if available
        has_detail_fields = any(
            project.get(k) for k in ["system_details", "required_features", "target_users", "current_issues"]
        )
        if has_detail_fields or project.get("details"):
            console.print("\n[bold cyan]発注の詳細[/bold cyan]")
            if project.get("system_details"):
                console.print(f"  [dim]システム詳細:[/dim] {project['system_details']}")
            if project.get("required_features"):
                console.print(f"  [dim]必須機能:[/dim] {project['required_features']}")
            if project.get("target_users"):
                console.print(f"  [dim]対象ユーザー:[/dim] {project['target_users']}")
            if project.get("current_issues"):
                console.print(f"  [dim]課題:[/dim] {project['current_issues']}")
            if project.get("development_type"):
                console.print(f"  [dim]開発種別:[/dim] {project['development_type']}")

        # Budget and schedule
        if project.get("budget") or project.get("delivery") or project.get("schedule"):
            console.print("\n[bold cyan]予算・スケジュール[/bold cyan]")
            if project.get("budget"):
                console.print(f"  予算: {project['budget']}")
            if project.get("budget_certainty"):
                console.print(f"  予算確度: {project['budget_certainty']}")
            if project.get("delivery"):
                console.print(f"  納期: {project['delivery']}")
            if project.get("schedule"):
                console.print(f"  スケジュール: {project['schedule']}")

        # Contact preferences
        if project.get("meeting_method") or project.get("contact_hours"):
            console.print("\n[bold cyan]商談情報[/bold cyan]")
            if project.get("meeting_method"):
                console.print(f"  打ち合わせ方法: {project['meeting_method']}")
            if project.get("contact_hours"):
                console.print(f"  連絡可能時間: {project['contact_hours']}")
            if project.get("preferred_times"):
                console.print(f"  商談希望日: {project['preferred_times']}")

        # Show messages
        messages = project.get("messages", [])
        if messages:
            console.print(f"\n[bold cyan]メッセージ ({len(messages)}件)[/bold cyan]\n")
            for msg in messages:
                sender = msg.get("sender", "Unknown")
                date = msg.get("date", "—")
                console.print(f"[cyan]{sender}[/cyan] [dim]({date})[/dim]")
                # Indent message content
                content = msg.get("content", "")
                for line in content.split("\n"):
                    console.print(f"  {line}")
                console.print()


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
