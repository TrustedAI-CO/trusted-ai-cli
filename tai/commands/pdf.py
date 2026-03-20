"""tai pdf — compile Markdown/Typst to branded PDF."""

from __future__ import annotations

import json
import shutil
import tempfile
import tomllib
from pathlib import Path

import typer
from rich.console import Console

from tai.core.context import get_ctx
from tai.core.errors import (
    TaiError,
    TemplateError,
    TemplateNotFoundError,
    TypstError,
    handle_error,
)
from tai.core.prompt import is_interactive, search_select
from tai.core.templates import (
    brand_install_dir,
    discover_templates,
    find_brand_source,
    find_template_source,
    install_brand,
    install_templates,
    remove_templates,
    templates_install_dir,
    validate_template_name,
)

_CMARKER_PACKAGE = "@preview/cmarker:0.1.8"

app = typer.Typer(
    name="pdf",
    help="Compile Markdown or Typst files to branded PDF.",
)
console = Console()
err_console = Console(stderr=True)


# ── setup-templates ──────────────────────────────────────────────────────────


@app.command("setup-templates")
def setup_templates(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Overwrite existing templates."),
    list_templates: bool = typer.Option(
        False, "--list", "-l", help="List available templates without installing."
    ),
    remove: bool = typer.Option(
        False, "--remove", "-r", help="Remove all installed templates."
    ),
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """Install or update bundled Typst templates and brand assets."""
    app_ctx = get_ctx(ctx)
    use_json = app_ctx.json_output or json_output

    try:
        if list_templates:
            _list_templates(use_json)
            return

        if remove:
            _remove_templates(use_json)
            return

        _install_templates(force, use_json)

    except TemplateError as exc:
        handle_error(exc)


def _list_templates(use_json: bool) -> None:
    """Show available templates without installing."""
    source = find_template_source()
    if source is None:
        if use_json:
            print(json.dumps({"templates": []}))
        else:
            console.print("[dim]No bundled templates found.[/dim]")
        return

    templates = discover_templates(source)
    if use_json:
        print(json.dumps({
            "templates": [
                {"name": t.name, "version": t.version, "description": t.description}
                for t in templates
            ],
        }))
    else:
        for t in templates:
            console.print(f"  [bold]{t.name}[/bold] v{t.version} — {t.description}")


def _remove_templates(use_json: bool) -> None:
    """Remove installed templates and brand assets."""
    count = remove_templates()
    brand = brand_install_dir()
    if brand.is_dir():
        shutil.rmtree(brand)

    if use_json:
        print(json.dumps({"removed": count}))
    elif count == 0:
        console.print("[dim]No installed templates found.[/dim]")
    else:
        console.print(f"Removed {count} template(s).")


def _install_templates(force: bool, use_json: bool) -> None:
    """Install templates and brand assets."""
    source = find_template_source()
    if source is None:
        raise TemplateError(
            "Cannot find bundled templates",
            hint="Run from the project repo or install tai with pip.",
        )

    result = install_templates(source, force=force)

    brand_source = find_brand_source()
    if brand_source is not None:
        install_brand(brand_source)

    if use_json:
        print(json.dumps({
            "installed": result.installed,
            "skipped": result.skipped,
            "install_path": str(templates_install_dir()),
        }))
        return

    for name in result.installed:
        console.print(f"  [green]\u2713[/green] {name}")
    for name in result.skipped:
        console.print(f"  [dim]  {name}[/dim] (exists, use --force)")

    console.print(
        f"\n[green]{len(result.installed)} template(s) installed[/green]"
        f", {len(result.skipped)} skipped"
        f" \u2014 {templates_install_dir()}"
    )

    if brand_source is not None:
        console.print(f"[green]Brand assets installed[/green] \u2014 {brand_install_dir()}")

    console.print(
        "[dim]Re-run with --force after upgrading tai to refresh templates.[/dim]"
    )


# ── templates ────────────────────────────────────────────────────────────────


@app.command("templates")
def templates_cmd(
    json_output: bool = typer.Option(False, "--json", help="JSON output."),
) -> None:
    """List installed templates."""
    install_dir = templates_install_dir()
    templates = discover_templates(install_dir) if install_dir.is_dir() else []

    if json_output:
        print(json.dumps({
            "templates": [
                {"name": t.name, "version": t.version, "description": t.description}
                for t in templates
            ],
        }))
        return

    if not templates:
        console.print("[dim]No templates installed.[/dim]")
        console.print("[dim]Hint: run [cyan]tai pdf setup-templates[/cyan] first.[/dim]")
        return

    for t in templates:
        console.print(f"  [bold]{t.name}[/bold] v{t.version} — {t.description}")


# ── compile ──────────────────────────────────────────────────────────────────


@app.command("compile")
def compile_cmd(
    ctx: typer.Context,
    file: Path = typer.Argument(..., help="Input .md or .typ file."),
    template: str | None = typer.Option(
        None, "--template", "-t", help="Template name to apply (for .md files)."
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output PDF path."
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Keep intermediate .typ file."
    ),
) -> None:
    """Compile a Markdown or Typst file to PDF."""
    from tai.core import typst as typst_mod

    try:
        typst_bin = typst_mod.find_typst()
        typst_mod.check_version(typst_bin)

        if not file.is_file():
            raise TypstError(
                f"File not found: {file}",
                hint="Check the file path and try again.",
            )

        suffix = file.suffix.lower()
        output_path = output or file.with_suffix(".pdf")

        if suffix == ".typ":
            result = typst_mod.compile_document(typst_bin, file, output_path)
            console.print(f"[green]\u2713[/green] {result.output_path}")
            return

        if suffix not in (".md", ".markdown"):
            raise TypstError(
                f"Unsupported file type: {suffix}",
                hint="Supported: .md, .markdown, .typ",
            )

        _compile_markdown(
            typst_bin, file, output_path, template_name=template, debug=debug
        )

    except (TypstError, TemplateError) as exc:
        handle_error(exc)


def _template_label(t: "TemplateInfo") -> str:
    return f"{t.name} — {t.description}" if t.description else t.name


def _pick_template() -> str | None:
    """Prompt the user to pick an installed template, or return None.

    In non-interactive terminals, raises TemplateError with available names.
    When no templates are installed, raises TemplateError with setup hint.
    """
    from tai.core.templates import TemplateInfo

    install_dir = templates_install_dir()
    templates = discover_templates(install_dir) if install_dir.is_dir() else []

    if not templates:
        raise TemplateError(
            "No templates installed",
            hint="Run: tai pdf setup-templates",
        )

    if not is_interactive():
        names = ", ".join(t.name for t in templates)
        raise TemplateError(
            "No --template specified and terminal is not interactive",
            hint=f"Use: --template <name>. Available: {names}",
        )

    chosen = search_select("Template:", templates, label_fn=_template_label)
    return chosen.name if chosen is not None else None


def _compile_markdown(
    typst_bin: Path,
    md_file: Path,
    output_path: Path,
    *,
    template_name: str | None,
    debug: bool,
) -> None:
    """Convert markdown to PDF, optionally applying a template."""
    from tai.core import typst as typst_mod

    md_content = md_file.read_text(encoding="utf-8")

    if not md_content.strip():
        err_console.print("[yellow]Warning:[/yellow] Input file is empty.")

    resolved_template = template_name
    if resolved_template is None:
        resolved_template = _pick_template()

    if resolved_template is not None:
        if not validate_template_name(resolved_template):
            raise TemplateError(
                f"Invalid template name: {resolved_template}",
                hint="Template names may only contain letters, numbers, hyphens, and underscores.",
            )

        template_dir = templates_install_dir() / resolved_template
        if not template_dir.is_dir():
            raise TemplateNotFoundError(resolved_template)

        typ_content = _wrap_md_with_template(md_file, template_dir)
    else:
        err_console.print(
            "[yellow]Warning:[/yellow] No --template specified. "
            "Compiling plain markdown without branding."
        )
        typ_content = _wrap_md_plain(md_file)

    tmp_dir = None
    try:
        if debug:
            typ_path = output_path.with_suffix(".typ")
        else:
            tmp_dir = tempfile.mkdtemp(prefix="tai-pdf-")
            typ_path = Path(tmp_dir) / "document.typ"

        typ_path.write_text(typ_content, encoding="utf-8")

        # Use filesystem root so Typst can access template libs, brand
        # assets, and the input MD file regardless of their locations.
        root = Path("/")
        result = typst_mod.compile_document(typst_bin, typ_path, output_path, root=root)

        console.print(f"[green]\u2713[/green] {result.output_path}")
        if debug:
            console.print(f"[dim]Intermediate: {typ_path}[/dim]")

    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _escape_typst_string(value: str) -> str:
    """Escape a string for safe inclusion in Typst source code."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _wrap_md_with_template(md_file: Path, template_dir: Path) -> str:
    """Generate a .typ file that imports the template and renders markdown."""
    md_abs = md_file.resolve().as_posix()
    brand_dir = brand_install_dir()
    brand_toml = brand_dir / "brand.toml"

    # Always define defaults so the template show rule works regardless of brand config
    company_name = "TrustedAI"
    company_tagline = None
    primary_color = None
    secondary_color = None

    if brand_toml.is_file():
        with brand_toml.open("rb") as f:
            brand = tomllib.load(f)
        company = brand.get("company", {})
        if company.get("name"):
            company_name = company["name"]
        if company.get("tagline"):
            company_tagline = company["tagline"]
        colors = brand.get("colors", {})
        if colors.get("primary"):
            primary_color = colors["primary"]
        if colors.get("secondary"):
            secondary_color = colors["secondary"]

    brand_vars = f'#let company-name = "{_escape_typst_string(company_name)}"\n'
    brand_vars += "#let company-logo = none\n"
    if company_tagline:
        brand_vars += f'#let company-tagline = "{_escape_typst_string(company_tagline)}"\n'
    if primary_color:
        brand_vars += f'#let primary-color = rgb("{_escape_typst_string(primary_color)}")\n'
    if secondary_color:
        brand_vars += f'#let secondary-color = rgb("{_escape_typst_string(secondary_color)}")\n'

    logo_path = brand_dir / "logo.png"
    if logo_path.is_file():
        brand_vars += f'#let company-logo = image("{logo_path.as_posix()}")\n'

    lib_path = (template_dir / "lib.typ").as_posix()

    return (
        f'#import "{lib_path}": *\n'
        f"\n"
        f"{brand_vars}"
        f"\n"
        f"#show: doc => template(doc, company-name: company-name, logo: company-logo)\n"
        f"\n"
        f'#{{  import "{_CMARKER_PACKAGE}"\n'
        f'   cmarker.render(read("{md_abs}"), smart-punctuation: true)\n'
        f"}}\n"
    )


def _wrap_md_plain(md_file: Path) -> str:
    """Generate a .typ file that renders plain markdown (no template)."""
    md_abs = md_file.resolve().as_posix()
    return (
        f'#{{  import "{_CMARKER_PACKAGE}"\n'
        f'   cmarker.render(read("{md_abs}"), smart-punctuation: true)\n'
        f"}}\n"
    )
