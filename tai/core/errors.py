"""Custom exceptions with user-friendly messages."""

import sys
import typer
from rich.console import Console

err_console = Console(stderr=True)


class TaiError(Exception):
    """Base error for all tai exceptions."""

    exit_code: int = 1

    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message)
        self.hint = hint


class AuthError(TaiError):
    """Authentication failed or token expired."""

    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, hint="Run: tai auth login")


class AuthExpiredError(AuthError):
    def __init__(self):
        super().__init__("Session expired", )
        self.hint = "Run: tai auth login"


class DomainError(AuthError):
    def __init__(self, email: str, domain: str):
        TaiError.__init__(
            self,
            f"Account {email} is not from @{domain}",
            hint=f"Sign in with your @{domain} Google account",
        )


class ConfigError(TaiError):
    """Invalid or missing configuration."""


class SecretNotFoundError(TaiError):
    def __init__(self, name: str):
        super().__init__(f"Secret '{name}' not found", hint="Run: tai secret set " + name)


class ProjectError(TaiError):
    """Invalid or missing project manifest (.tai.toml)."""

    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message, hint=hint or "Run: tai project init")


class ApiError(TaiError):
    """Company API returned an error."""

    def __init__(self, status: int, body: str):
        super().__init__(f"API error {status}: {body}")
        self.exit_code = 2


def handle_error(exc: TaiError) -> None:
    """Print error + hint to stderr and exit with appropriate code."""
    err_console.print(f"[bold red]Error:[/bold red] {exc}")
    if exc.hint:
        err_console.print(f"[dim]Hint: {exc.hint}[/dim]")
    raise typer.Exit(exc.exit_code)
