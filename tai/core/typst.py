"""Typst binary detection, version checking, and compilation."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from tai.core.errors import (
    TypstCompileError,
    TypstError,
    TypstNotFoundError,
    TypstVersionError,
)

MIN_TYPST_VERSION = "0.12.0"


@dataclass(frozen=True)
class CompileResult:
    output_path: Path
    stderr: str


def find_typst() -> Path:
    """Locate the typst binary in PATH.

    Raises TypstNotFoundError if not found.
    """
    binary = shutil.which("typst")
    if binary is None:
        raise TypstNotFoundError()
    return Path(binary)


def parse_version(version_output: str) -> str:
    """Extract version number from `typst --version` output."""
    match = re.search(r"(\d+\.\d+\.\d+)", version_output)
    return match.group(1) if match else "0.0.0"


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split("."))


def check_version(typst_bin: Path, minimum: str = MIN_TYPST_VERSION) -> str:
    """Verify typst version meets minimum requirement.

    Returns the installed version string.
    Raises TypstVersionError if too old, TypstNotFoundError if binary disappeared.
    """
    try:
        result = subprocess.run(
            [str(typst_bin), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        raise TypstNotFoundError() from None
    except subprocess.TimeoutExpired:
        raise TypstError(
            "Typst version check timed out",
            hint="Verify your Typst installation is working.",
        ) from None

    installed = parse_version(result.stdout)
    if _version_tuple(installed) < _version_tuple(minimum):
        raise TypstVersionError(installed, minimum)
    return installed


def compile_document(
    typst_bin: Path,
    input_path: Path,
    output_path: Path,
    *,
    root: Path | None = None,
) -> CompileResult:
    """Run typst compile and return the result.

    Raises TypstCompileError on non-zero exit or timeout.
    """
    cmd = [str(typst_bin), "compile", str(input_path), str(output_path)]
    if root is not None:
        cmd.extend(["--root", str(root)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise TypstNotFoundError() from None
    except subprocess.TimeoutExpired:
        raise TypstCompileError("Compilation timed out (120s limit)") from None

    if result.returncode != 0:
        raise TypstCompileError(result.stderr.strip())

    return CompileResult(output_path=output_path, stderr=result.stderr)
