"""tai style — matplotlib style management commands."""

from __future__ import annotations

import typer
from rich.console import Console

from tai.core.style import StyleInstallError, install

app = typer.Typer(
    name="style",
    help="Manage TrustedAI matplotlib chart styles.",
)
console = Console()
err_console = Console(stderr=True)


@app.command("install")
def install_cmd() -> None:
    """Install the TrustedAI matplotlib style to your local stylelib.

    After running this, use the style in any Python script:

        import matplotlib.pyplot as plt
        plt.style.use('trustedai')
    """
    try:
        dest = install()
    except StyleInstallError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Installed[/green] trustedai.mplstyle → {dest}")
    console.print("[dim]Usage: plt.style.use('trustedai')[/dim]")
