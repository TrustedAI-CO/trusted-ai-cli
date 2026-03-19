"""Custom exceptions with user-friendly messages."""

import sys
import typer
from rich.console import Console

err_console = Console(stderr=True)


class ExitCode:
    SUCCESS = 0
    ERROR = 1
    USAGE = 2
    NOT_FOUND = 3
    PERMISSION_DENIED = 4
    CONFLICT = 5


class TaiError(Exception):
    """Base error for all tai exceptions."""

    exit_code: int = ExitCode.ERROR

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


class SkillError(TaiError):
    """Skill installation or update failed."""


class TypstError(TaiError):
    """Base for Typst-related errors."""


class TypstNotFoundError(TypstError):
    exit_code: int = ExitCode.NOT_FOUND

    def __init__(self) -> None:
        super().__init__(
            "Typst not found in PATH",
            hint="Install: brew install typst (or cargo install typst-cli)",
        )


class TypstVersionError(TypstError):
    def __init__(self, installed: str, required: str) -> None:
        super().__init__(
            f"Typst {installed} is too old (requires >= {required})",
            hint="Upgrade: brew upgrade typst (or cargo install typst-cli)",
        )


class TypstCompileError(TypstError):
    def __init__(self, stderr: str) -> None:
        super().__init__("Typst compilation failed", hint=stderr)


class TemplateError(TaiError):
    """Template installation or resolution failed."""


class TemplateNotFoundError(TemplateError):
    exit_code: int = ExitCode.NOT_FOUND

    def __init__(self, name: str) -> None:
        super().__init__(
            f"Template '{name}' not found",
            hint="Run: tai pdf setup-templates",
        )


class ApiError(TaiError):
    """Company API returned an error."""

    def __init__(self, status: int, body: str):
        super().__init__(f"API error {status}: {body}")
        if status == 404:
            self.exit_code = ExitCode.NOT_FOUND
        elif status == 403:
            self.exit_code = ExitCode.PERMISSION_DENIED
        elif status == 409:
            self.exit_code = ExitCode.CONFLICT
        else:
            self.exit_code = ExitCode.USAGE


def handle_error(exc: TaiError) -> None:
    """Print error + hint to stderr and exit with appropriate code."""
    err_console.print(f"[bold red]Error:[/bold red] {exc}")
    if exc.hint:
        err_console.print(f"[dim]Hint: {exc.hint}[/dim]")
    raise typer.Exit(exc.exit_code)
