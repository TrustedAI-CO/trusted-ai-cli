"""tai claude — manage Claude Code authentication and hooks."""

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

app = typer.Typer(name="claude", help="Manage Claude Code authentication and hooks.")
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


# ── Hook management ──────────────────────────────────────────────────────────


@app.command(name="setup-hooks")
def setup_hooks(
    ctx: typer.Context,
    list_hooks: bool = typer.Option(
        False, "--list", "-l", help="List available hooks without installing."
    ),
    remove: bool = typer.Option(
        False, "--remove", "-r", help="Remove all tai-managed hooks."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON."
    ),
) -> None:
    """Install tai Claude Code hooks into ~/.claude/settings.json.

    Hooks provide automated quality checks, session management, and
    developer experience improvements for Claude Code sessions.

    Run without flags to install.  Use --list to preview, --remove to uninstall.
    """
    from tai.hooks import load_hook_definitions

    if not shutil.which("node"):
        err_console.print(
            "[bold red]Error:[/bold red] 'node' not found in PATH."
        )
        err_console.print(
            "[dim]Hint: Hooks require Node.js — https://nodejs.org[/dim]"
        )
        raise typer.Exit(1)

    definitions = load_hook_definitions()

    # --list: show available hooks and exit
    if list_hooks:
        _print_hook_list(definitions, json_output)
        return

    # --remove: strip tai hooks from settings
    if remove:
        _remove_hooks(json_output)
        return

    # Default: install hooks
    _install_hooks(definitions, json_output)


def _print_hook_list(
    definitions: dict, json_output: bool
) -> None:
    """Print available hooks grouped by event type."""
    if json_output:
        flat = []
        for event_type, entries in definitions.items():
            for entry in entries:
                flat.append({
                    "event": event_type,
                    "matcher": entry.get("matcher", "*"),
                    "description": entry.get("description", ""),
                })
        print(json.dumps(flat, indent=2))
        return

    for event_type, entries in definitions.items():
        console.print(f"\n[bold]{event_type}[/bold]")
        for entry in entries:
            matcher = entry.get("matcher", "*")
            desc = entry.get("description", "").removeprefix("[tai] ")
            console.print(f"  [{matcher}] {desc}")


def _remove_hooks(json_output: bool) -> None:
    """Remove tai-managed hooks from settings.json."""
    from tai.hooks import (
        is_tai_hook,
        read_settings,
        remove_tai_hooks,
        write_settings,
    )

    try:
        settings = read_settings()
    except json.JSONDecodeError:
        _abort_bad_json()

    existing_hooks = settings.get("hooks", {})
    tai_count = sum(
        1
        for entries in existing_hooks.values()
        for e in entries
        if is_tai_hook(e)
    )

    if tai_count == 0:
        if json_output:
            print(json.dumps({"removed": 0}))
        else:
            console.print("[dim]No tai-managed hooks found.[/dim]")
        return

    cleaned = remove_tai_hooks(existing_hooks)
    updated_settings = {**settings, "hooks": cleaned}
    # Remove empty hooks key
    if not cleaned:
        updated_settings.pop("hooks", None)
    write_settings(updated_settings)

    if json_output:
        print(json.dumps({"removed": tai_count}))
    else:
        console.print(f"Removed {tai_count} tai-managed hook(s).")


def _install_hooks(
    definitions: dict, json_output: bool
) -> None:
    """Resolve and install hooks into settings.json."""
    from tai.hooks import (
        merge_hooks,
        read_settings,
        resolve_hooks,
        write_settings,
    )

    try:
        settings = read_settings()
    except json.JSONDecodeError:
        _abort_bad_json()

    resolved = resolve_hooks(definitions)
    existing_hooks = settings.get("hooks", {})
    merged = merge_hooks(existing_hooks, resolved)

    updated_settings = {**settings, "hooks": merged}
    write_settings(updated_settings)

    total = sum(len(entries) for entries in resolved.values())

    if json_output:
        print(json.dumps({
            "installed": total,
            "events": {k: len(v) for k, v in resolved.items()},
        }))
    else:
        console.print(f"\nInstalled {total} hook(s):\n")
        for event_type, entries in resolved.items():
            console.print(f"  [bold]{event_type}[/bold]: {len(entries)}")
        console.print(
            "\n[dim]Hooks are active in new Claude Code sessions.[/dim]"
        )
        console.print(
            "[dim]Re-run after upgrading tai to refresh hook scripts.[/dim]"
        )


def _abort_bad_json() -> None:
    from tai.hooks import SETTINGS_PATH

    err_console.print(
        f"[bold red]Error:[/bold red] {SETTINGS_PATH} contains invalid JSON."
    )
    err_console.print("[dim]Hint: Fix the JSON syntax and try again.[/dim]")
    raise typer.Exit(1)
