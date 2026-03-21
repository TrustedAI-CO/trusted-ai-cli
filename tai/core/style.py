"""TrustedAI matplotlib style — palette constants and style installer.

Color palette derived from tai/templates/typst/theme.typ.
Keep in sync with: theme.typ, tai/data/styles/trustedai.mplstyle

Usage::

    from tai.core.style import PALETTE, COLORS, install

    # Install once (or run `tai style install`):
    install()

    # Then in any script:
    import matplotlib.pyplot as plt
    plt.style.use('trustedai')
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

_log = logging.getLogger(__name__)

# ── Brand palette (from theme.typ) ──────────────────────────────────────────

COLORS: dict[str, str] = {
    "navy": "#1a1a6c",
    "blue": "#2d4a9f",
    "sky": "#5b7fd9",
    "accent": "#e85d3a",
    "amber": "#d4a03c",
    "teal": "#2a9d8f",
    "warm": "#f4f1eb",
    "light": "#f8f6f2",
    "dark": "#1f2937",
    "gray": "#6b7280",
    "muted": "#9ca3af",
    "border": "#d1d5db",
}

# Ordered cycle for multi-series charts — matches axes.prop_cycle in .mplstyle
PALETTE: list[str] = [
    COLORS["navy"],
    COLORS["blue"],
    COLORS["sky"],
    COLORS["accent"],
    COLORS["amber"],
    COLORS["teal"],
]

# ── Bundled .mplstyle asset path ────────────────────────────────────────────

_STYLE_FILE = Path(__file__).resolve().parent.parent / "data" / "styles" / "trustedai.mplstyle"


class StyleInstallError(Exception):
    """Raised when matplotlib style installation fails."""


def _get_stylelib_dir() -> Path:
    """Return the matplotlib stylelib directory, creating it if needed."""
    try:
        import matplotlib as mpl
    except ImportError as exc:
        raise StyleInstallError(
            "matplotlib is not installed. Install it first:\n"
            "  pip install matplotlib"
        ) from exc

    stylelib = Path(mpl.get_configdir()) / "stylelib"
    return stylelib


def install() -> Path:
    """Copy the TrustedAI .mplstyle file to matplotlib's stylelib directory.

    Returns the destination path on success.
    """
    if not _STYLE_FILE.is_file():
        raise StyleInstallError(
            f"Bundled style file not found: {_STYLE_FILE}\n"
            "Reinstall tai to restore it."
        )

    stylelib = _get_stylelib_dir()

    try:
        stylelib.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StyleInstallError(
            f"Failed to create stylelib directory: {stylelib}\n{exc}"
        ) from exc

    dest = stylelib / _STYLE_FILE.name

    try:
        shutil.copy2(_STYLE_FILE, dest)
    except PermissionError as exc:
        raise StyleInstallError(
            f"Cannot write to {dest}. Check file permissions."
        ) from exc
    except OSError as exc:
        raise StyleInstallError(
            f"Failed to copy style file to {dest}\n{exc}"
        ) from exc

    _log.info("Installed %s → %s", _STYLE_FILE.name, dest)
    return dest
