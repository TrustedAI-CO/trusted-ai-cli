"""AppContext — central state stored in typer.Context.obj and accessed via get_ctx()."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from tai.core.config import ProfileConfig, TaiConfig


@dataclass
class AppContext:
    profile: str = "default"
    verbose: bool = False
    json_output: bool = False
    config: "TaiConfig | None" = field(default=None, repr=False)

    def active_profile(self) -> "ProfileConfig":
        from tai.core.config import ProfileConfig
        if self.config is None:
            return ProfileConfig()
        return self.config.active()


def get_ctx(typer_ctx: typer.Context) -> AppContext:
    """Extract AppContext from a typer.Context. Always safe to call."""
    if isinstance(typer_ctx.obj, AppContext):
        return typer_ctx.obj
    return AppContext()
