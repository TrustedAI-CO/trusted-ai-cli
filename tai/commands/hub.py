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
        from tai.core.auth import get_id_token
        id_token = get_id_token(app_ctx.profile, profile_cfg.oauth_client_id)
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


def _hub_json(client: httpx.Client, method: str, url: str, **kwargs):
    """Execute Hub request and return parsed JSON."""
    resp = _hub_request(client, method, url, **kwargs)
    return resp.json()


# ── Project resolution ───────────────────────────────────────────────────────


_UUID_RE = __import__("re").compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", __import__("re").IGNORECASE,
)


def _resolve_project(ctx: typer.Context, project: str | None) -> str:
    """Resolve a project ID or prefix to a spaceId. Interactive picker when None and TTY."""
    if project and _UUID_RE.match(project):
        return project

    client = _hub_client(ctx)
    spaces = _hub_json(client, "GET", "/api/hub/spaces")
    projects = [s for s in spaces if s.get("type") == "project"]

    if project:
        prefix = project.lower()
        matches = [p for p in projects if p["id"].startswith(prefix)]
        if len(matches) == 1:
            return matches[0]["id"]
        if len(matches) > 1:
            err_console.print(f"[bold red]Error:[/bold red] Ambiguous prefix '{project}':")
            for m in matches:
                err_console.print(f"  - {m['name']} ({m['id']})")
            raise typer.Exit(ExitCode.CONFLICT)
        err_console.print(f"[bold red]Error:[/bold red] No project matching ID prefix '{project}'.")
        raise typer.Exit(ExitCode.NOT_FOUND)

    if not is_interactive():
        err_console.print("[bold red]Error:[/bold red] --project required in non-interactive mode.")
        raise typer.Exit(ExitCode.USAGE)

    chosen = search_select("Project:", projects, label_fn=lambda p: f"{p['name']} ({p['id'][:8]})")
    if chosen is None:
        raise typer.Exit(0)
    return chosen["id"]


def _resolve_wiki(ctx: typer.Context) -> str:
    """Return the first wiki space ID."""
    client = _hub_client(ctx)
    spaces = _hub_json(client, "GET", "/api/hub/spaces")
    wikis = [s for s in spaces if s.get("type") == "wiki"]
    if not wikis:
        err_console.print("[bold red]Error:[/bold red] No wiki space found.")
        raise typer.Exit(ExitCode.NOT_FOUND)
    return wikis[0]["id"]


def _resolve_private(ctx: typer.Context) -> str:
    """Return the user's private space ID."""
    client = _hub_client(ctx)
    spaces = _hub_json(client, "GET", "/api/hub/spaces")
    privates = [s for s in spaces if s.get("type") == "private"]
    if not privates:
        err_console.print("[bold red]Error:[/bold red] No private space found.")
        raise typer.Exit(ExitCode.NOT_FOUND)
    return privates[0]["id"]


def _resolve_page_space(ctx: typer.Context, project: str | None, private: bool) -> str:
    """Resolve space for page commands: --project > --private > wiki (default)."""
    if project:
        return _resolve_project(ctx, project)
    if private:
        return _resolve_private(ctx)
    return _resolve_wiki(ctx)


def _resolve_task_ref(ctx: typer.Context, ref: str, space_id: str | None = None) -> str:
    """Resolve a task reference (#number or UUID) to a task ID."""
    if not ref.startswith("#"):
        return ref

    number = ref.lstrip("#")
    client = _hub_client(ctx)
    params: dict[str, str] = {}
    if space_id:
        params["spaceId"] = space_id
    tasks = _hub_json(client, "GET", "/api/hub/tasks", params=params)
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
            ", ".join(t.get("assignees", [])) or "—",
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
    results = _hub_json(client, "GET", "/api/hub/search", params={"q": query})

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(results))
        return

    if not results:
        console.print("[dim]No results found.[/dim]")
        return

    for item in results:
        if isinstance(item, str):
            console.print(f"  {item}")
        else:
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
    spaces = _hub_json(client, "GET", "/api/hub/spaces")
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
    data = _hub_json(client, "GET", "/api/hub/summary")

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
        return

    if not data:
        console.print("[dim]No workspace data.[/dim]")
        return

    for space in data:
        status_str = f" ({space['status']})" if space.get("status") else ""
        console.print(f"\n[bold]{space['name']}[/bold] [{space['type']}]{status_str}")
        counts = space.get("taskCounts")
        if counts:
            console.print(f"  Tasks: {counts['total']} (todo:{counts['todo']} in-progress:{counts['in-progress']} review:{counts['review']} done:{counts['done']})")
        pages = space.get("pageCount", 0)
        if pages:
            console.print(f"  Pages: {pages}")
        for ms in space.get("milestones", []):
            due = f" due:{ms['dueDate']}" if ms.get("dueDate") else ""
            console.print(f"  Milestone: {ms['title']} [{ms['status']}] {ms['doneTasks']}/{ms['totalTasks']}{due}")


# ── Page commands ────────────────────────────────────────────────────────────

page_app = typer.Typer(name="page", help="Manage pages.")
app.add_typer(page_app)


@page_app.callback(invoke_without_command=True)
def list_pages(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    private: bool = typer.Option(False, "--private", help="List pages in private space."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List pages. Default: wiki. Use --project or --private to scope."""
    if ctx.invoked_subcommand is not None:
        return

    space_id = _resolve_page_space(ctx, project, private)
    client = _hub_client(ctx)
    pages = _hub_json(client, "GET", "/api/hub/pages", params={"spaceId": space_id})

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
    page = _hub_json(client, "GET", f"/api/hub/page/{id_or_title}")

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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    private: bool = typer.Option(False, "--private", help="Create in private space."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Create a new page. Default: wiki. Use --project or --private to scope."""
    space_id = _resolve_page_space(ctx, project, private)
    client = _hub_client(ctx)
    page = _hub_json(client, "POST", "/api/hub/page", json={"spaceId": space_id, "title": title})

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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
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

    tasks = _hub_json(client, "GET", "/api/hub/tasks", params=params)

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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
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

    task = _hub_json(client, "POST", "/api/hub/task", json=body)

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(task))
    else:
        number = task.get("number", "")
        console.print(f"[green]Created[/green] #{number} — {title}")


@task_app.command("update")
def task_update(
    ctx: typer.Context,
    ref: Annotated[str, typer.Argument(help="Task reference (#number or UUID).")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or name (required for #number refs)."),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status."),
    title: Optional[str] = typer.Option(None, "--title", help="New title."),
    priority: Optional[str] = typer.Option(None, "--priority", help="New priority."),
    due: Optional[str] = typer.Option(None, "--due", help="New due date (YYYY-MM-DD)."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Update an existing task."""
    space_id = _resolve_project(ctx, project) if ref.startswith("#") else None
    task_id = _resolve_task_ref(ctx, ref, space_id)
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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List project members."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    member_list = _hub_json(client, "GET", "/api/hub/members", params={"spaceId": space_id})

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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List project milestones."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    milestone_list = _hub_json(client, "GET", "/api/hub/milestones", params={"spaceId": space_id})

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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or name (required for #number refs)."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List deliverables for a task."""
    space_id = _resolve_project(ctx, project) if ref.startswith("#") else None
    task_id = _resolve_task_ref(ctx, ref, space_id)
    client = _hub_client(ctx)
    data = _hub_json(client, "GET", "/api/hub/deliverables", params={"taskId": task_id})

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
        return

    formatted = data.get("formatted", "") if isinstance(data, dict) else str(data)
    if not formatted or "No deliverables" in formatted:
        console.print("[dim]No deliverables found.[/dim]")
    else:
        console.print(formatted)


@app.command()
def comment(
    ctx: typer.Context,
    target_type: Annotated[str, typer.Argument(help="Target type (task, page).")],
    ref: Annotated[str, typer.Argument(help="Target reference (#number, UUID, or page ID).")],
    body: Annotated[str, typer.Argument(help="Comment body.")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or name (required for #number refs)."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Add a comment to a task or page."""
    if target_type == "task":
        space_id = _resolve_project(ctx, project) if ref.startswith("#") else None
        target_id = _resolve_task_ref(ctx, ref, space_id)
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
        mime = f.get("mimeType", "")
        is_folder = mime == "application/vnd.google-apps.folder"
        name = f"📁 {f.get('name', '')}" if is_folder else f.get("name", "")
        display_type = "folder" if is_folder else mime.split("/")[-1] if "/" in mime else mime
        size = "—" if is_folder else f.get("size", "0")
        table.add_row(f.get("id", "")[:12], name, display_type, size)
    console.print(table)
    console.print("[dim]Use --folder <ID> to browse subfolders.[/dim]")


@file_app.callback(invoke_without_command=True)
def list_files(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    folder: Optional[str] = typer.Option(None, "--folder", "-f", help="Folder ID to browse into."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List files in a project's Drive folder. Use --folder to browse subfolders."""
    if ctx.invoked_subcommand is not None:
        return

    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    params: dict[str, str] = {"spaceId": space_id}
    if folder:
        params["folderId"] = folder
    data = _hub_json(client, "GET", "/api/drive/list", params=params)
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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    folder: Optional[str] = typer.Option(None, "--folder", "-f", help="Target folder ID."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Upload a file to project Drive folder. Use --folder for subfolders."""
    if not path.exists():
        err_console.print(f"[bold red]Error:[/bold red] File not found: {path}")
        raise typer.Exit(ExitCode.ERROR)

    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)

    form_data: dict[str, str] = {"spaceId": space_id}
    if folder:
        form_data["folderId"] = folder

    with open(path, "rb") as f:
        resp = client.post(
            "/api/drive/upload",
            files={"file": (path.name, f)},
            data=form_data,
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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
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
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
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


# ── Meeting commands ────────────────────────────────────────────────────────

meeting_app = typer.Typer(name="meeting", help="Manage project meetings.")
app.add_typer(meeting_app)


def _print_meetings_table(meetings: list[dict]) -> None:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Summary")
    table.add_column("Start", style="dim")
    table.add_column("End", style="dim")
    table.add_column("Meeting URL", style="dim")
    table.add_column("Linked By", style="dim")
    for m in meetings:
        table.add_row(
            m.get("id", ""),
            m.get("summary", ""),
            m.get("startTime", ""),
            m.get("endTime", ""),
            m.get("meetingUrl") or "—",
            m.get("linkedByName") or "—",
        )
    console.print(table)


@meeting_app.callback(invoke_without_command=True)
def list_meetings(
    ctx: typer.Context,
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List meetings linked to a project."""
    if ctx.invoked_subcommand is not None:
        return

    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)
    meetings = _hub_json(client, "GET", "/api/hub/meetings", params={"spaceId": space_id})

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(meetings))
        return

    if not meetings:
        console.print("[dim]No meetings linked.[/dim]")
        return

    _print_meetings_table(meetings)


@meeting_app.command("link")
def meeting_link(
    ctx: typer.Context,
    event_id: Annotated[str, typer.Argument(help="Google Calendar event ID (from 'tai hub cal').")],
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project ID or prefix."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Link a calendar event to a project. Event details fetched from Google Calendar automatically."""
    space_id = _resolve_project(ctx, project)
    client = _hub_client(ctx)

    result = _hub_json(client, "POST", "/api/hub/meeting", json={
        "spaceId": space_id,
        "calendarEventId": event_id,
    })

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(result))
    else:
        console.print(f"[green]Linked[/green] \"{result.get('summary', '')}\" — id:{result.get('id', '')[:8]}")


@meeting_app.command("unlink")
def meeting_unlink(
    ctx: typer.Context,
    meeting_id: Annotated[str, typer.Argument(help="Meeting link UUID (from list).")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Unlink a meeting from its project."""
    client = _hub_client(ctx)
    resp = _hub_request(client, "DELETE", f"/api/hub/meeting/{meeting_id}")

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(resp.json() if resp.text.strip() else {}))
    else:
        console.print(f"[green]Unlinked[/green] meeting {meeting_id[:8]}.")


# ── Email commands ──────────────────────────────────────────────────────────

email_app = typer.Typer(name="email", help="Manage email (Gmail).")
app.add_typer(email_app)


@email_app.callback(invoke_without_command=True)
def email_search(
    ctx: typer.Context,
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Gmail search query."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Search email threads. Default: recent inbox."""
    if ctx.invoked_subcommand is not None:
        return

    client = _hub_client(ctx)
    params: dict[str, str] = {}
    if query:
        params["q"] = query
    data = _hub_json(client, "GET", "/api/email/threads", params=params)
    threads = data.get("threads", data) if isinstance(data, dict) else data

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(threads))
        return

    if not threads:
        console.print("[dim]No emails found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Subject")
    table.add_column("From", style="dim")
    table.add_column("Date", style="dim")
    table.add_column("", style="dim")
    for t in threads:
        unread = "[bold cyan]●[/bold cyan]" if t.get("unread") else ""
        table.add_row(
            t.get("id", "")[:12],
            t.get("subject", ""),
            t.get("from", ""),
            t.get("date", ""),
            unread,
        )
    console.print(table)


@email_app.command("read")
def email_read(
    ctx: typer.Context,
    thread_id: Annotated[str, typer.Argument(help="Thread ID from search results.")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Read an email thread."""
    client = _hub_client(ctx)
    data = _hub_json(client, "GET", f"/api/email/threads/{thread_id}")

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
        return

    console.print(f"[bold]{data.get('subject', '')}[/bold]\n")
    for msg in data.get("messages", []):
        console.print(f"[dim]--- {msg.get('from', '')} ({msg.get('date', '')}) ---[/dim]")
        body = msg.get("bodyText") or msg.get("bodyHtml", "")
        console.print(body[:2000])
        console.print()


@email_app.command("drafts")
def email_drafts(
    ctx: typer.Context,
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List email drafts."""
    client = _hub_client(ctx)
    data = _hub_json(client, "GET", "/api/email/drafts")
    drafts = data.get("drafts", data) if isinstance(data, dict) else data

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(drafts))
        return

    if not drafts:
        console.print("[dim]No drafts.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Subject")
    table.add_column("To", style="dim")
    for d in drafts:
        table.add_row(d.get("id", "")[:12], d.get("subject", ""), d.get("to", ""))
    console.print(table)


@email_app.command("draft")
def email_create_draft(
    ctx: typer.Context,
    to: Annotated[str, typer.Argument(help="Recipient email.")],
    subject: Annotated[str, typer.Argument(help="Subject line.")],
    body: Annotated[str, typer.Argument(help="Email body.")],
    cc: Optional[str] = typer.Option(None, "--cc", help="CC recipients."),
    bcc: Optional[str] = typer.Option(None, "--bcc", help="BCC recipients."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Create an email draft (does not send)."""
    client = _hub_client(ctx)
    payload: dict = {"to": to, "subject": subject, "body": body}
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc

    data = _hub_json(client, "POST", "/api/email/drafts", json=payload)

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
    else:
        console.print(f"[green]Draft created[/green] — {data.get('draftId', '')[:12]}")


@email_app.command("send")
def email_send(
    ctx: typer.Context,
    to: Annotated[str, typer.Argument(help="Recipient email.")],
    subject: Annotated[str, typer.Argument(help="Subject line.")],
    body: Annotated[str, typer.Argument(help="Email body.")],
    cc: Optional[str] = typer.Option(None, "--cc", help="CC recipients."),
    bcc: Optional[str] = typer.Option(None, "--bcc", help="BCC recipients."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Send an email."""
    client = _hub_client(ctx)
    payload: dict = {"to": to, "subject": subject, "body": body}
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc

    data = _hub_json(client, "POST", "/api/email/send", json=payload)

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
    else:
        console.print(f"[green]Sent[/green] to {to}")


@email_app.command("reply-context")
def email_reply_context(
    ctx: typer.Context,
    message_id: Annotated[str, typer.Argument(help="Message ID (from email read).")],
    reply_all: bool = typer.Option(False, "--all", help="Reply-all context."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Get reply context for composing a response."""
    client = _hub_client(ctx)
    params = {"messageId": message_id}
    if reply_all:
        params["replyAll"] = "true"
    data = _hub_json(client, "GET", "/api/email/reply-context", params=params)

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
        return

    console.print(f"  To: {data.get('to', '')}")
    console.print(f"  Cc: {data.get('cc', '')}")
    console.print(f"  Subject: {data.get('subject', '')}")


# ── Calendar commands ───────────────────────────────────────────────────────

cal_app = typer.Typer(name="cal", help="Manage calendar events.")
app.add_typer(cal_app)


@cal_app.callback(invoke_without_command=True)
def cal_list(
    ctx: typer.Context,
    from_date: Optional[str] = typer.Option(None, "--from", help="Start date (ISO 8601)."),
    to_date: Optional[str] = typer.Option(None, "--to", help="End date (ISO 8601)."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List calendar events. Default: next 7 days."""
    if ctx.invoked_subcommand is not None:
        return

    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    time_min = from_date or now.isoformat()
    time_max = to_date or (now + timedelta(days=7)).isoformat()

    client = _hub_client(ctx)
    data = _hub_json(client, "GET", "/api/calendar/events", params={"timeMin": time_min, "timeMax": time_max})
    events = data.get("events", data) if isinstance(data, dict) else data

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(events))
        return

    if not events:
        console.print("[dim]No events found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Event")
    table.add_column("Start", style="dim")
    table.add_column("End", style="dim")
    table.add_column("Status", style="dim")
    for e in events:
        start_raw = e.get("start", "")
        end_raw = e.get("end", "")
        start_str = (start_raw if isinstance(start_raw, str) else start_raw.get("dateTime", start_raw.get("date", "")))[:16]
        end_str = (end_raw if isinstance(end_raw, str) else end_raw.get("dateTime", end_raw.get("date", "")))[:16]
        table.add_row(
            e.get("id", "")[:12],
            e.get("summary", ""),
            start_str,
            end_str,
            e.get("responseStatus", e.get("status", "")),
        )
    console.print(table)


@cal_app.command("create")
def cal_create(
    ctx: typer.Context,
    title: Annotated[str, typer.Argument(help="Event title.")],
    start: Annotated[str, typer.Argument(help="Start time (ISO 8601).")],
    end: Annotated[str, typer.Argument(help="End time (ISO 8601).")],
    description: Optional[str] = typer.Option(None, "--desc", help="Event description."),
    location: Optional[str] = typer.Option(None, "--location", help="Location."),
    all_day: bool = typer.Option(False, "--all-day", help="All-day event."),
    timezone_str: Optional[str] = typer.Option(None, "--tz", help="Timezone (e.g. Asia/Tokyo)."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Create a calendar event."""
    client = _hub_client(ctx)
    payload: dict = {"summary": title, "start": start, "end": end}
    if description:
        payload["description"] = description
    if location:
        payload["location"] = location
    if all_day:
        payload["allDay"] = True
    if timezone_str:
        payload["timeZone"] = timezone_str

    data = _hub_json(client, "POST", "/api/calendar/events", json=payload)
    event = data.get("event", data) if isinstance(data, dict) else data

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(event))
    else:
        console.print(f"[green]Created[/green] event — {title}")


@cal_app.command("update")
def cal_update(
    ctx: typer.Context,
    event_id: Annotated[str, typer.Argument(help="Event ID.")],
    title: Optional[str] = typer.Option(None, "--title", help="New title."),
    start: Optional[str] = typer.Option(None, "--start", help="New start (ISO 8601)."),
    end: Optional[str] = typer.Option(None, "--end", help="New end (ISO 8601)."),
    description: Optional[str] = typer.Option(None, "--desc", help="New description."),
    location: Optional[str] = typer.Option(None, "--location", help="New location."),
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Update a calendar event."""
    client = _hub_client(ctx)
    payload: dict = {}
    if title:
        payload["summary"] = title
    if start:
        payload["start"] = start
    if end:
        payload["end"] = end
    if description:
        payload["description"] = description
    if location:
        payload["location"] = location

    if not payload:
        err_console.print("[bold red]Error:[/bold red] No fields to update.")
        raise typer.Exit(ExitCode.USAGE)

    data = _hub_json(client, "PUT", f"/api/calendar/events/{event_id}", json=payload)
    event = data.get("event", data) if isinstance(data, dict) else data

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(event))
    else:
        console.print(f"[green]Updated[/green] event {event_id[:12]}.")


@cal_app.command("rsvp")
def cal_rsvp(
    ctx: typer.Context,
    event_id: Annotated[str, typer.Argument(help="Event ID.")],
    response: Annotated[str, typer.Argument(help="Response: accepted, declined, tentative.")],
    json_flag: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Respond to a calendar event invitation."""
    if response not in ("accepted", "declined", "tentative"):
        err_console.print("[bold red]Error:[/bold red] Response must be: accepted, declined, or tentative.")
        raise typer.Exit(ExitCode.USAGE)

    client = _hub_client(ctx)
    data = _hub_json(client, "PATCH", f"/api/calendar/events/{event_id}", json={"response": response})

    if _is_json(ctx, json_flag):
        console.print_json(json.dumps(data))
    else:
        console.print(f"[green]{response.capitalize()}[/green] event {event_id[:12]}.")
