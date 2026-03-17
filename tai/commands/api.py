"""tai api — call any company API endpoint, list available endpoints."""

import json
from typing import Optional

import typer
from rich.console import Console

from tai.core.context import get_ctx
from tai.core.errors import handle_error, TaiError
from tai.core.http import build_client

app = typer.Typer(name="api", help="Call company API endpoints directly.")
console = Console()
err_console = Console(stderr=True)

_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@app.command("call")
def call(
    ctx: typer.Context,
    path: str = typer.Argument(help="API path, e.g. /users/me"),
    method: str = typer.Option("GET", "--method", "-X", help="HTTP method"),
    data: Optional[str] = typer.Option(None, "--data", "-d", help="JSON request body"),
    query: Optional[list[str]] = typer.Option(None, "--param", "-p", help="Query params: key=value"),
):
    """Call a company API endpoint.

    Examples:\n
      tai api call /users/me\n
      tai api call /deployments -X POST -d '{"service": "api"}'\n
      tai api call /events -p status=active -p limit=10
    """
    app_ctx = get_ctx(ctx)
    method = method.upper()
    if method not in _METHODS:
        err_console.print(f"Unknown method: {method}. Use one of: {', '.join(_METHODS)}")
        raise typer.Exit(1)

    params = {}
    if query:
        for item in query:
            if "=" not in item:
                err_console.print(f"Invalid param format '{item}'. Use key=value.")
                raise typer.Exit(1)
            k, v = item.split("=", 1)
            params[k] = v

    body = None
    if data:
        try:
            body = json.loads(data)
        except json.JSONDecodeError as e:
            err_console.print(f"Invalid JSON body: {e}")
            raise typer.Exit(1)

    try:
        resp = build_client(app_ctx).request(method, path, params=params or None, json=body)
        ct = resp.headers.get("content-type", "")
        output = resp.json() if "application/json" in ct else resp.text

        if app_ctx.json_output or isinstance(output, (dict, list)):
            console.print_json(json.dumps(output))
        else:
            console.print(output)
    except TaiError as e:
        handle_error(e)


@app.command("endpoints")
def list_endpoints(ctx: typer.Context):
    """List available API endpoints from the OpenAPI spec."""
    app_ctx = get_ctx(ctx)
    try:
        spec = build_client(app_ctx).get("/openapi.json").json()
        paths = spec.get("paths", {})

        if app_ctx.json_output:
            console.print_json(json.dumps(list(paths.keys())))
            return

        for path, methods in paths.items():
            for m in methods:
                if m.upper() in _METHODS:
                    summary = methods[m].get("summary", "")
                    console.print(f"  [bold cyan]{m.upper():6}[/bold cyan]  {path}  [dim]{summary}[/dim]")
    except TaiError as e:
        handle_error(e)
