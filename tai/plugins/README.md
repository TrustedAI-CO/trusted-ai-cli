# Writing a tai Plugin

A plugin is a Python package that adds a new command group to `tai`.

## Minimal Example

```python
# tai_myteam/commands.py
import typer
from tai.core.context import AppContext, pass_context

app = typer.Typer(name="myteam", help="MyTeam-specific commands.")

@app.command()
@pass_context
def deploy(ctx: AppContext, service: str):
    """Deploy a service."""
    ...
```

```toml
# pyproject.toml of your plugin package
[project.entry-points."tai.plugins"]
myteam = "tai_myteam.commands:app"
```

After `pip install tai-myteam`, the `tai myteam deploy` command is available automatically — no changes to this repo needed.
