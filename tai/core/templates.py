"""Template discovery, parsing, and installation to ~/.tai/templates/."""

from __future__ import annotations

import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

TEMPLATES_DIR_NAME = "templates"
BRAND_DIR_NAME = "brand"
_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


@dataclass(frozen=True)
class TemplateInfo:
    name: str
    version: str
    description: str
    path: Path


@dataclass(frozen=True)
class InstallResult:
    installed: list[str]
    skipped: list[str]


def validate_template_name(name: str) -> bool:
    """Check that a template name is safe (no path traversal)."""
    return bool(_VALID_NAME_RE.match(name)) and ".." not in name


def parse_typst_toml(typst_toml: Path) -> TemplateInfo:
    """Parse a typst.toml manifest file."""
    with typst_toml.open("rb") as f:
        data = tomllib.load(f)

    package = data.get("package", {})
    name = package.get("name", typst_toml.parent.name)
    version = package.get("version", "0.0.0")
    description = package.get("description", "")
    return TemplateInfo(
        name=name,
        version=version,
        description=description,
        path=typst_toml.parent,
    )


def discover_templates(source_dir: Path) -> list[TemplateInfo]:
    """Find all templates (subdirectories with typst.toml) in source_dir."""
    templates: list[TemplateInfo] = []
    if not source_dir.is_dir():
        return templates
    for child in sorted(source_dir.iterdir()):
        manifest = child / "typst.toml"
        if child.is_dir() and manifest.is_file():
            try:
                templates.append(parse_typst_toml(manifest))
            except (tomllib.TOMLDecodeError, KeyError):
                continue
    return templates


def _find_data_source(package: str, repo_subpath: str) -> Path | None:
    """Locate bundled data: try package data first, then repo root."""
    try:
        from importlib.resources import files

        pkg_path = files(package)
        resolved = Path(str(pkg_path))
        if resolved.is_dir() and any(resolved.iterdir()):
            return resolved
    except (ImportError, ModuleNotFoundError, TypeError):
        pass

    repo_root = _find_repo_root()
    if repo_root:
        candidate = repo_root / repo_subpath
        if candidate.is_dir():
            return candidate
    return None


def find_template_source() -> Path | None:
    """Locate bundled Typst templates."""
    return _find_data_source("tai.templates.typst", "tai/templates/typst")


def find_brand_source() -> Path | None:
    """Locate bundled brand assets."""
    return _find_data_source("tai.templates.typst.brand", "tai/templates/typst/brand")


def _find_repo_root() -> Path | None:
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def templates_install_dir() -> Path:
    """Base directory for installed templates: ~/.tai/templates/."""
    return Path.home() / ".tai" / TEMPLATES_DIR_NAME


def brand_install_dir() -> Path:
    """Base directory for installed brand assets: ~/.tai/brand/."""
    return Path.home() / ".tai" / BRAND_DIR_NAME


def install_templates(source_dir: Path, *, force: bool = False) -> InstallResult:
    """Install templates to ~/.tai/templates/.

    Copies both shared files (theme.typ, brand/, etc.) and template
    subdirectories (article/, report/, slides/) so that relative imports
    like ``#import "../theme.typ"`` resolve correctly.

    When force=True, existing templates are overwritten.
    """
    base = templates_install_dir()
    base.mkdir(parents=True, exist_ok=True)

    # Install shared files (*.typ at source root, brand/ directory)
    for item in source_dir.iterdir():
        if item.name == "examples":
            continue
        dest = base / item.name
        if item.is_file():
            if dest.exists() and not force:
                continue
            shutil.copy2(item, dest)
        elif item.is_dir() and not (item / "typst.toml").is_file():
            # Non-template directory (e.g. brand/)
            if dest.exists() and force:
                shutil.rmtree(dest)
            if not dest.exists():
                shutil.copytree(item, dest)

    # Install template packages (subdirectories with typst.toml)
    templates = discover_templates(source_dir)
    installed: list[str] = []
    skipped: list[str] = []

    for template in templates:
        if not validate_template_name(template.name):
            skipped.append(template.name)
            continue

        dest = base / template.name

        if dest.exists() and not force:
            skipped.append(template.name)
            continue

        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(template.path, dest)
        installed.append(template.name)

    return InstallResult(installed=installed, skipped=skipped)


def install_brand(source_dir: Path) -> None:
    """Install brand assets to ~/.tai/brand/."""
    dest = brand_install_dir()
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source_dir, dest)


def remove_templates() -> int:
    """Remove all installed templates. Returns count of removed templates."""
    base = templates_install_dir()
    if not base.is_dir():
        return 0
    count = 0
    for child in base.iterdir():
        if child.is_dir() and (child / "typst.toml").is_file():
            shutil.rmtree(child)
            count += 1
    return count
