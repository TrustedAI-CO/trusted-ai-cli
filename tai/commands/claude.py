"""tai claude — manage Claude Code authentication and skills."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import sys
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import typer
from rich.console import Console

from tai.core.context import get_ctx
from tai.core.errors import SkillError, handle_error
from tai.core.skills import find_skill_source, install_skills, skills_install_dir

app = typer.Typer(name="claude", help="Manage Claude Code authentication and skills.")
console = Console()
err_console = Console(stderr=True)

_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
_AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
_REDIRECT_URI = "https://platform.claude.com/oauth/code/callback"
_SCOPES = "org:create_api_key user:profile user:inference user:sessions:claude_code user:mcp_servers"


def _code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _build_auth_url(verifier: str, state: str) -> str:
    params = {
        "code": "true",
        "client_id": _CLIENT_ID,
        "response_type": "code",
        "redirect_uri": _REDIRECT_URI,
        "scope": _SCOPES,
        "code_challenge": _code_challenge(verifier),
        "code_challenge_method": "S256",
        "state": state,
    }
    return _AUTHORIZE_URL + "?" + urlencode(params)


def _parse_auth_code(user_input: str) -> str:
    """Accept a full callback URL, code#state string, or bare code."""
    text = user_input.strip()
    if text.startswith("http"):
        parsed = urlparse(text)
        qs = parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        if not code:
            raise ValueError("No 'code' parameter found in URL.")
        return code
    if "#" in text:
        return text.split("#", 1)[0]
    return text


def _exchange_code(code: str, verifier: str, state: str) -> dict:
    resp = httpx.post(
        _TOKEN_URL,
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _REDIRECT_URI,
            "client_id": _CLIENT_ID,
            "code_verifier": verifier,
            "state": state,
        },
        headers={"Content-Type": "application/json"},
        timeout=15.0,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Token exchange failed ({resp.status_code}): {resp.text}")
    return resp.json()


@app.command()
def login(ctx: typer.Context) -> None:
    """Authenticate Claude Code via browser OAuth.

    Generates a login URL for you to open in a browser.
    After authorizing, paste the callback URL (or code) shown on the page.
    """
    claude_bin = shutil.which("claude")
    if not claude_bin:
        err_console.print("[bold red]Error:[/bold red] 'claude' not found in PATH.")
        err_console.print("[dim]Hint: Install Claude Code — https://claude.ai/code[/dim]")
        raise typer.Exit(1)

    verifier = _code_verifier()
    state = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    auth_url = _build_auth_url(verifier, state)

    console.print("\n[bold]Login URL:[/bold]")
    console.print(f"  [cyan]{auth_url}[/cyan]\n")
    console.print(
        "[dim]Steps:\n"
        "  1. Open the URL in a browser and sign in.\n"
        "  2. After authorizing you will be redirected to a page on\n"
        "     platform.claude.com — copy the [bold]full URL[/bold] from\n"
        "     your browser's address bar (or just the code shown on the page).\n"
        "  3. Paste it below.[/dim]\n"
    )

    raw = typer.prompt("Paste callback URL or code")

    try:
        code = _parse_auth_code(raw)
    except ValueError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1)

    console.print("Exchanging authorization code…")
    try:
        token_data = _exchange_code(code, verifier, state)
    except RuntimeError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1)

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        err_console.print("[bold red]Error:[/bold red] No refresh token in response.")
        raise typer.Exit(1)

    # Let claude handle profile fetch, API-key creation, onboarding, etc.
    scopes = token_data.get("scope", _SCOPES)
    console.print("Completing authentication…")
    env = os.environ.copy()
    env["CLAUDE_CODE_OAUTH_REFRESH_TOKEN"] = refresh_token
    env["CLAUDE_CODE_OAUTH_SCOPES"] = scopes

    result = subprocess.run([claude_bin, "auth", "login"], env=env)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def logout(ctx: typer.Context) -> None:
    """Sign out of Claude Code."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        err_console.print("[bold red]Error:[/bold red] 'claude' not found in PATH.")
        raise typer.Exit(1)

    result = subprocess.run([claude_bin, "auth", "logout"])
    raise typer.Exit(result.returncode)


@app.command()
def status(ctx: typer.Context) -> None:
    """Show Claude Code authentication status."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        err_console.print("[bold red]Error:[/bold red] 'claude' not found in PATH.")
        raise typer.Exit(1)

    result = subprocess.run([claude_bin, "auth", "status"])
    raise typer.Exit(result.returncode)


@app.command("setup-skills")
def setup_skills(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Overwrite existing skills."),
    json_flag: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Install or update bundled Claude Code skills as tai-* personal skills."""
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
            console.print(f"  [dim]  {name}[/dim] (exists, use --force)")

        console.print(
            f"\n[green]{len(result.installed)} skill(s) installed[/green]"
            f", {len(result.skipped)} skipped"
            f" — {skills_install_dir()}"
        )
        console.print("[dim]Restart Claude Code to pick up new skills.[/dim]")

    except SkillError as exc:
        handle_error(exc)
