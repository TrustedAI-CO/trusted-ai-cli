"""tai hub — manage workspace projects, pages, tasks, and members via Hub API."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated, Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from tai.core import keystore
from tai.core.context import AppContext, get_ctx
from tai.core.errors import ExitCode
from tai.core.prompt import is_interactive, search_select

log = logging.getLogger(__name__)

console = Console()
err_console = Console(stderr=True)

app = typer.Typer(name="hub", help="Manage workspace via Hub.")


# ── Hub HTTP client ──────────────────────────────────────────────────────────


def _hub_client(ctx: typer.Context) -> httpx.Client:
    """Build an HTTP client pointed at Hub with id_token auth."""
    app_ctx = get_ctx(ctx)
    profile_cfg = app_ctx.active_profile()
    hub_url = getattr(profile_cfg, "hub_base_url", None) or "https://hub.trusted-ai.internal"

    try:
        id_token = keystore.retrieve(app_ctx.profile, "id_token")
    except Exception:
        err_console.print("[bold red]Error:[/bold red] Not authenticated.")
        err_console.print("[dim]Hint: Run: tai login[/dim]")
        raise typer.Exit(ExitCode.ERROR)

    return httpx.Client(
        base_url=hub_url,
        headers={
            "Authorization": f"Bearer {id_token}",
            "Accept": "application/json",
        },
        timeout=profile_cfg.timeout_seconds,
    )


def _hub_request(client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
    """Execute a Hub request with standard error handling."""
    try:
        resp = client.request(method, url, **kwargs)
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        err_console.print(f"[bold red]Error:[/bold red] Cannot reach Hub: {exc}")
        raise typer.Exit(ExitCode.ERROR)

    if resp.status_code == 401:
        err_console.print("[bold red]Error:[/bold red] Hub session expired.")
        err_console.print("[dim]Hint: Run: tai login[/dim]")
        raise typer.Exit(ExitCode.ERROR)
    if resp.status_code >= 400:
        try:
            body = resp.json().get("error", resp.text)
        except Exception:
            body = resp.text
        err_console.print(f"[bold red]Error:[/bold red] Hub API {resp.status_code}: {body}")
        code = {
            403: ExitCode.PERMISSION_DENIED,
            404: ExitCode.NOT_FOUND,
            409: ExitCode.CONFLICT,
        }.get(resp.status_code, ExitCode.ERROR)
        raise typer.Exit(code)

    return resp


# ── Project resolution ───────────────────────────────────────────────────────


def _resolve_project(ctx: typer.Context, name: str | None) -> str:
    """Resolve a project name to a spaceId. Interactive picker when name is None and TTY."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/hub/spaces")
    spaces = resp.json()
    projects = [s for s in spaces if s.get("type") == "project"]

    if name:
        lower_name = name.lower()
        exact = [p for p in projects if p["name"].lower() == lower_name]
        if exact:
            return exact[0]["id"]
        matches = [p for p in projects if lower_name in p["name"].lower()]
        if len(matches) == 1:
            return matches[0]["id"]
        if len(matches) == 0:
            err_console.print(f"[bold red]Error:[/bold red] No project matching '{name}'.")
            raise typer.Exit(ExitCode.NOT_FOUND)
        err_console.print(f"[bold red]Error:[/bold red] Ambiguous — {len(matches)} projects match '{name}':")
        for m in matches:
            err_console.print(f"  - {m['name']}")
        raise typer.Exit(ExitCode.CONFLICT)

    if not is_interactive():
        err_console.print("[bold red]Error:[/bold red] --project required in non-interactive mode.")
        raise typer.Exit(ExitCode.USAGE)

    chosen = search_select("Project:", projects, label_fn=lambda p: p["name"])
    if chosen is None:
        raise typer.Exit(0)
    return chosen["id"]


def _resolve_task_ref(ctx: typer.Context, ref: str, space_id: str | None = None) -> str:
    """Resolve a task reference (#number or UUID) to a task ID."""
    if not ref.startswith("#"):
        return ref

    number = ref.lstrip("#")
    client = _hub_client(ctx)
    params: dict[str, str] = {}
    if space_id:
        params["spaceId"] = space_id
    resp = _hub_request(client, "GET", "/api/hub/tasks", params=params)
    tasks = resp.json()
    matches = [t for t in tasks if str(t.get("number")) == number]
    if not matches:
        err_console.print(f"[bold red]Error:[/bold red] No task found with number {ref}.")
        raise typer.Exit(ExitCode.NOT_FOUND)
    return matches[0]["id"]


def _is_json(ctx: typer.Context, json_flag: bool) -> bool:
    return json_flag or getattr(get_ctx(ctx), "json_output", False)


# ── Table printers ───────────────────────────────────────────────────────────


def _print_projects_table(projects: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Name")
    table.add_column("Status", style="dim")
    table.add_column("Repos", style="dim", justify="right")
    for p in projects:
        table.add_row(
            p.get("name", ""),
            p.get("status", "—"),
            str(p.get("repoCount", 0)),
        )
    console.print(table)


def _print_tasks_table(tasks: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Priority", style="dim")
    table.add_column("Assignees", style="dim")
    for t in tasks:
        status = t.get("status", "—")
        style = "green" if status == "done" else ""
        table.add_row(
            str(t.get("number", "")),
            t.get("title", ""),
            f"[{style}]{status}[/{style}]" if style else status,
            t.get("priority") or "—",
            ", ".join(
                a.get("name", a.get("userId", "")) for a in t.get("assignees", [])
            ) or "—",
        )
    console.print(table)


def _print_pages_table(pages: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Title")
    table.add_column("Parent", style="dim")
    for p in pages:
        table.add_row(
            p.get("id", "")[:8],
            p.get("title", ""),
            p.get("parentId", "—") or "—",
        )
    console.print(table)


def _print_members_table(members: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Name")
    table.add_column("Email", style="dim")
    table.add_column("Role", style="dim")
    for m in members:
        table.add_row(
            m.get("name", ""),
            m.get("email", ""),
            m.get("role", "—"),
        )
    console.print(table)


def _print_milestones_table(milestones: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Title")
    table.add_column("Status", style="dim")
    table.add_column("Due", style="dim")
    table.add_column("Progress", style="dim")
    for m in milestones:
        total = m.get("totalTasks", 0)
        done = m.get("doneTasks", 0)
        progress = f"{done}/{total}" if total else "—"
        table.add_row(
            m.get("title", ""),
            m.get("status", "—"),
            m.get("dueDate") or "—",
            progress,
        )
    console.print(table)


# ── Global commands ──────────────────────────────────────────────────────────


@app.command()
def search(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Search query.")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Search across the workspace."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/hub/search", params={"q": query})
    data = resp.json()
    results = data.get("results", data) if isinstance(data, dict) else data

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(results))
        return

    if not results:
        console.print("[dim]No results found.[/dim]")
        return

    for item in results:
        title = item.get("title") or item.get("name") or "—"
        kind = item.get("type", "")
        console.print(f"  [{kind}] {title}")


@app.command()
def projects(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List workspace projects."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/hub/spaces")
    spaces = resp.json()
    project_list = [s for s in spaces if s.get("type") == "project"]

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(project_list))
        return

    if not project_list:
        console.print("[dim]No projects found.[/dim]")
        return

    _print_projects_table(project_list)


@app.command()
def summary(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show workspace summary."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/hub/summary")

    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        data = resp.json()
        if _is_json(ctx, json_flag):
            console.print_json(json.dumps(data))
        else:
            lines = data.get("lines", []) if isinstance(data, dict) else []
            for line in lines:
                console.print(line)
    else:
        text = resp.text
        if _is_json(ctx, json_flag):
            console.print_json(json.dumps({"text": text}))
        else:
            console.print(text)


# ── Page commands ────────────────────────────────────────────────────────────

page_app = typer.Typer(name="page", help="Manage pages.")
app.add_typer(page_app)


@page_app.callback(invoke_without_command=True)
def list_pages(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List pages, optionally filtered by project."""
    if ctx.invoked_subcommand is not None:
        return

    client = _hub_client(ctx)
    params: dict[str, str] = {}
    if project:
        space_id = _resolve_project(ctx, project)
        params["spaceId"] = space_id

    resp = _hub_request(client, "GET", "/api/hub/pages", params=params)
    pages = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(pages))
        return

    if not pages:
        console.print("[dim]No pages found.[/dim]")
        return

    _print_pages_table(pages)


@page_app.command("get")
def page_get(
    ctx: typer.Context,
    id_or_title: Annotated[str, typer.Argument(help="Page ID or title.")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Get a page by ID or title."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", f"/api/hub/page/{id_or_title}")
    page = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(page))
        return

    console.print(f"[bold]{page.get('title', '')}[/bold]")
    content = page.get("content", "")
    if content:
        console.print()
        console.print(content)


@page_app.command("create")
def page_create(
    ctx: typer.Context,
    title: Annotated[str, typer.Argument(help="Page title.")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Create a new page."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    resp = _hub_request(client, "POST", "/api/hub/page", json={"spaceId": space_id, "title": title})
    page = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(page))
    else:
        console.print(f"[green]Created[/green] page {page.get('id', '')[:8]} — {title}")


@page_app.command("update")
def page_update(
    ctx: typer.Context,
    id_or_title: Annotated[str, typer.Argument(help="Page ID or title.")],
    content: Annotated[str, typer.Argument(help="New page content.")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Update page content."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "POST", f"/api/hub/page/{id_or_title}/content", json={"content": content})

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(resp.json() if resp.text.strip() else {}))
    else:
        console.print(f"[green]Updated[/green] page content.")


@page_app.command("rename")
def page_rename(
    ctx: typer.Context,
    id_or_title: Annotated[str, typer.Argument(help="Page ID or title.")],
    new_title: Annotated[str, typer.Argument(help="New title.")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Rename a page."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "POST", f"/api/hub/page/{id_or_title}/title", json={"title": new_title})

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(resp.json() if resp.text.strip() else {}))
    else:
        console.print(f"[green]Renamed[/green] page to '{new_title}'.")


# ── Task commands ────────────────────────────────────────────────────────────

task_app = typer.Typer(name="task", help="Manage tasks.")
app.add_typer(task_app)


@task_app.callback(invoke_without_command=True)
def list_tasks(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List tasks for a project."""
    if ctx.invoked_subcommand is not None:
        return

    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    params: dict[str, str] = {"spaceId": space_id}
    if status:
        params["status"] = status

    resp = _hub_request(client, "GET", "/api/hub/tasks", params=params)
    tasks = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(tasks))
        return

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    _print_tasks_table(tasks)


@task_app.command("create")
def task_create(
    ctx: typer.Context,
    title: Annotated[str, typer.Argument(help="Task title.")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    priority: Optional[str] = typer.Option(None, "--priority", help="Task priority."),
    due: Optional[str] = typer.Option(None, "--due", help="Due date (YYYY-MM-DD)."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Create a new task."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)

    body: dict = {"spaceId": space_id, "title": title}
    if priority:
        body["priority"] = priority
    if due:
        body["dueDate"] = due

    resp = _hub_request(client, "POST", "/api/hub/task", json=body)
    task = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(task))
    else:
        number = task.get("number", "")
        console.print(f"[green]Created[/green] #{number} — {title}")


@task_app.command("update")
def task_update(
    ctx: typer.Context,
    ref: Annotated[str, typer.Argument(help="Task reference (#number or UUID).")],
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status."),
    title: Optional[str] = typer.Option(None, "--title", help="New title."),
    priority: Optional[str] = typer.Option(None, "--priority", help="New priority."),
    due: Optional[str] = typer.Option(None, "--due", help="New due date (YYYY-MM-DD)."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Update an existing task."""
    task_id = _resolve_task_ref(ctx, ref)
    client = _hub_client(ctx)

    body: dict = {}
    if status:
        body["status"] = status
    if title:
        body["title"] = title
    if priority:
        body["priority"] = priority
    if due:
        body["dueDate"] = due

    if not body:
        err_console.print("[bold red]Error:[/bold red] No fields to update. Use --status, --title, --priority, or --due.")
        raise typer.Exit(ExitCode.USAGE)

    resp = _hub_request(client, "POST", f"/api/hub/task/{task_id}", json=body)

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(resp.json() if resp.text.strip() else {}))
    else:
        console.print(f"[green]Updated[/green] task {ref}.")


# ── Project-scoped commands ──────────────────────────────────────────────────


@app.command()
def members(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List project members."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/hub/members", params={"spaceId": space_id})
    member_list = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(member_list))
        return

    if not member_list:
        console.print("[dim]No members found.[/dim]")
        return

    _print_members_table(member_list)


@app.command()
def milestones(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List project milestones."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/hub/milestones", params={"spaceId": space_id})
    milestone_list = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(milestone_list))
        return

    if not milestone_list:
        console.print("[dim]No milestones found.[/dim]")
        return

    _print_milestones_table(milestone_list)


@app.command()
def deliverables(
    ctx: typer.Context,
    ref: Annotated[str, typer.Argument(help="Task reference (#number or UUID).")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List deliverables for a task."""
    task_id = _resolve_task_ref(ctx, ref)
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/hub/deliverables", params={"taskId": task_id})
    data = resp.json()
    items = data.get("items", data) if isinstance(data, dict) else data

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(items))
        return

    if not items:
        console.print("[dim]No deliverables found.[/dim]")
        return

    for item in items:
        console.print(f"  - {item.get('title') or item.get('name') or item}")


@app.command()
def comment(
    ctx: typer.Context,
    target_type: Annotated[str, typer.Argument(help="Target type (task, page).")],
    ref: Annotated[str, typer.Argument(help="Target reference (#number, UUID, or page ID).")],
    body: Annotated[str, typer.Argument(help="Comment body.")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Add a comment to a task or page."""
    if target_type == "task":
        target_id = _resolve_task_ref(ctx, ref)
    else:
        target_id = ref

    client = _hub_client(ctx)
    resp = _hub_request(
        client, "POST", "/api/hub/comment",
        json={"targetType": target_type, "targetId": target_id, "body": body},
    )

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(resp.json() if resp.text.strip() else {}))
    else:
        console.print(f"[green]Comment added[/green] to {target_type} {ref}.")


# ── File commands ───────────────────────────────────────────────────────────

file_app = typer.Typer(name="file", help="Manage project files.")
app.add_typer(file_app)


def _print_files_table(files: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")
    table.add_column("Type", style="dim")
    table.add_column("Size", style="dim", justify="right")
    for f in files:
        table.add_row(
            f.get("id", "")[:12],
            f.get("name", ""),
            f.get("mimeType", ""),
            f.get("size", "0"),
        )
    console.print(table)


@file_app.callback(invoke_without_command=True)
def list_files(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List files in a project's Drive folder."""
    if ctx.invoked_subcommand is not None:
        return

    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    resp = _hub_request(client, "GET", "/api/drive/list", params={"spaceId": space_id})
    data = resp.json()
    files = data.get("files", [])

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(files))
        return

    if not files:
        console.print("[dim]No files found.[/dim]")
        return

    _print_files_table(files)


@file_app.command("search")
def file_search(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Search query.")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Search files by name."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    resp = _hub_request(
        client, "GET", "/api/hub/files/search",
        params={"spaceId": space_id, "q": query},
    )
    data = resp.json()
    files = data.get("files", [])

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(files))
        return

    if not files:
        console.print("[dim]No files found.[/dim]")
        return

    _print_files_table(files)


@file_app.command("upload")
def file_upload(
    ctx: typer.Context,
    path: Annotated[Path, typer.Argument(help="Path to the file to upload.")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Upload a file to project Drive folder."""
    if not path.exists():
        err_console.print(f"[bold red]Error:[/bold red] File not found: {path}")
        raise typer.Exit(ExitCode.ERROR)

    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)

    with open(path, "rb") as f:
        resp = client.post(
            "/api/drive/upload",
            files={"file": (path.name, f)},
            data={"spaceId": space_id},
        )

    if resp.status_code == 401:
        err_console.print("[bold red]Error:[/bold red] Hub session expired.")
        err_console.print("[dim]Hint: Run: tai login[/dim]")
        raise typer.Exit(ExitCode.ERROR)
    if resp.status_code >= 400:
        try:
            body = resp.json().get("error", resp.text)
        except Exception:
            body = resp.text
        err_console.print(f"[bold red]Error:[/bold red] Hub API {resp.status_code}: {body}")
        raise typer.Exit(ExitCode.ERROR)

    data = resp.json()

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
    else:
        uploaded = data.get("file", {})
        console.print(f"[green]Uploaded[/green] {uploaded.get('name', path.name)} ({uploaded.get('id', '')[:12]})")


@file_app.command("download")
def file_download(
    ctx: typer.Context,
    file_id: Annotated[str, typer.Argument(help="Drive file ID.")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output path."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Download a file from project Drive."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)

    with client.stream("GET", "/api/drive/download", params={"fileId": file_id, "spaceId": space_id}) as resp:
        if resp.status_code == 401:
            err_console.print("[bold red]Error:[/bold red] Hub session expired.")
            err_console.print("[dim]Hint: Run: tai login[/dim]")
            raise typer.Exit(ExitCode.ERROR)
        if resp.status_code >= 400:
            resp.read()
            err_console.print(f"[bold red]Error:[/bold red] Hub API {resp.status_code}")
            raise typer.Exit(ExitCode.ERROR)

        # Determine output filename from Content-Disposition or fallback
        disposition = resp.headers.get("content-disposition", "")
        filename = file_id
        if "filename=" in disposition:
            parts = disposition.split("filename=")
            if len(parts) > 1:
                filename = parts[1].split(";")[0].strip().strip('"')

        dest = output or Path(filename)

        with open(dest, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=8192):
                f.write(chunk)

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps({"path": str(dest)}))
    else:
        console.print(f"[green]Downloaded[/green] {dest}")


@file_app.command("delete")
def file_delete(
    ctx: typer.Context,
    file_id: Annotated[str, typer.Argument(help="Drive file ID.")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project name."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Delete a file from project Drive."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    resp = _hub_request(
        client, "DELETE", "/api/drive/delete",
        json={"fileId": file_id, "spaceId": space_id},
    )

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(resp.json() if resp.text.strip() else {}))
    else:
        console.print(f"[green]Deleted[/green] file {file_id[:12]}.")
