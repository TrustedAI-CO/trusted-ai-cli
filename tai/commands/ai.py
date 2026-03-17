"""tai ai — chat, complete, models."""

import json
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from tai.core.context import get_ctx
from tai.core.errors import handle_error, TaiError
from tai.core.http import build_client

app = typer.Typer(name="ai", help="Use company AI tools.")
console = Console()
err_console = Console(stderr=True)


@app.command()
def chat(
    ctx: typer.Context,
    message: str = typer.Argument(help="Message to send"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override AI model"),
    system: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output"),
):
    """Send a chat message to the company AI."""
    app_ctx = get_ctx(ctx)
    profile_cfg = app_ctx.active_profile()
    payload: dict = {
        "model": model or profile_cfg.ai_model,
        "messages": [{"role": "user", "content": message}],
        "stream": not no_stream and not app_ctx.json_output,
    }
    if system:
        payload["system"] = system

    try:
        client = build_client(app_ctx)
        if payload["stream"]:
            _stream_chat(client, payload)
        else:
            data = client.post("/ai/chat", json=payload).json()
            if app_ctx.json_output:
                console.print_json(json.dumps(data))
            else:
                console.print(Markdown(data.get("content", "")))
    except TaiError as e:
        handle_error(e)


def _stream_chat(client, payload: dict) -> None:
    with client.stream("POST", "/ai/chat", json=payload) as resp:
        for line in resp.iter_lines():
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    break
                try:
                    token = json.loads(chunk).get("delta", {}).get("text", "")
                    console.print(token, end="")
                except json.JSONDecodeError:
                    pass
    console.print()


@app.command()
def complete(
    ctx: typer.Context,
    prompt: str = typer.Argument(help="Completion prompt"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    max_tokens: int = typer.Option(1024, "--max-tokens"),
):
    """Generate a text completion."""
    app_ctx = get_ctx(ctx)
    profile_cfg = app_ctx.active_profile()
    payload = {"model": model or profile_cfg.ai_model, "prompt": prompt, "max_tokens": max_tokens}
    try:
        data = build_client(app_ctx).post("/ai/complete", json=payload).json()
        if app_ctx.json_output:
            console.print_json(json.dumps(data))
        else:
            console.print(data.get("text", ""))
    except TaiError as e:
        handle_error(e)


@app.command()
def models(ctx: typer.Context):
    """List available AI models."""
    app_ctx = get_ctx(ctx)
    try:
        data = build_client(app_ctx).get("/ai/models").json()
        if app_ctx.json_output:
            console.print_json(json.dumps(data))
            return
        for m in data.get("models", []):
            console.print(f"  [cyan]{m['id']}[/cyan]  {m.get('description', '')}")
    except TaiError as e:
        handle_error(e)
