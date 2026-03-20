"""tai pdf — compile Markdown/Typst to branded PDF."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

import typer
from rich.console import Console

from tai.core.context import get_ctx
from tai.core.config import load_brand_colors
from tai.core.errors import (
    MermaidError,
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
            result = typst_mod.compile_document(
                typst_bin, file.resolve(), output_path, root=Path("/"),
            )
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

    except (TypstError, TemplateError, MermaidError) as exc:
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

    from tai.core import mermaid as mermaid_mod

    md_content = md_file.read_text(encoding="utf-8")

    if not md_content.strip():
        err_console.print("[yellow]Warning:[/yellow] Input file is empty.")

    resolved_template = template_name
    if resolved_template is None:
        resolved_template = _pick_template()

    tmp_dir = None
    try:
        compile_md_file = md_file
        frontmatter: dict[str, str] | None = None

        # Render mermaid diagrams to SVG and replace with placeholders
        brand_toml = brand_install_dir() / "brand.toml"
        brand = load_brand_colors(brand_toml)
        mermaid_result = mermaid_mod.preprocess(md_content, brand=brand)
        md_content = mermaid_result.content
        has_mermaid = mermaid_result.has_diagrams

        if resolved_template is not None:
            if not validate_template_name(resolved_template):
                raise TemplateError(
                    f"Invalid template name: {resolved_template}",
                    hint="Template names may only contain letters, numbers, hyphens, and underscores.",
                )

            template_dir = templates_install_dir() / resolved_template
            if not template_dir.is_dir():
                raise TemplateNotFoundError(resolved_template)

            frontmatter = _parse_frontmatter(md_content)

            # Extract single H1 as title and promote headings for all templates
            promoted_body: str | None = None
            body = _strip_frontmatter_body(md_content)
            h1_title, promoted = _extract_single_h1(body)
            if h1_title is not None:
                if "title" not in frontmatter:
                    frontmatter["title"] = h1_title
                    md_content = _update_file_frontmatter(
                        md_file, md_content, frontmatter
                    )
                promoted_body = promoted

            # Prompt for missing frontmatter and update source file
            md_content, frontmatter = _ensure_frontmatter(
                md_file, md_content, frontmatter, resolved_template
            )

            # Write temp .md when content was modified (headings or mermaid)
            needs_temp = promoted_body is not None or has_mermaid
            if needs_temp:
                tmp_dir = tempfile.mkdtemp(prefix="tai-pdf-")
                tmp_md = Path(tmp_dir) / md_file.name
                if promoted_body is not None:
                    fm_text = (
                        _build_frontmatter_block(frontmatter) if frontmatter else ""
                    )
                    tmp_md.write_text(fm_text + promoted_body, encoding="utf-8")
                else:
                    tmp_md.write_text(md_content, encoding="utf-8")
                compile_md_file = tmp_md

            typ_content = _wrap_md_with_template(
                compile_md_file, template_dir, frontmatter=frontmatter
            )
        else:
            # No template — write temp file if mermaid changed content
            if has_mermaid:
                tmp_dir = tempfile.mkdtemp(prefix="tai-pdf-")
                tmp_md = Path(tmp_dir) / md_file.name
                tmp_md.write_text(md_content, encoding="utf-8")
                compile_md_file = tmp_md

            err_console.print(
                "[yellow]Warning:[/yellow] No --template specified. "
                "Compiling plain markdown without branding."
            )
            typ_content = _wrap_md_plain(compile_md_file)

        # Inject mermaid show rules before the content
        if has_mermaid:
            typ_content = mermaid_result.typst_show_rules() + typ_content

        if debug:
            typ_path = output_path.with_suffix(".typ")
        else:
            if tmp_dir is None:
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
    """Escape a string for safe inclusion in a Typst string literal.

    Inside Typst "..." strings, only backslash and double-quote need
    escaping.  Other Typst markup characters (#, $, @, <, >) are NOT
    interpreted inside string literals, so they are safe as-is.
    """
    return value.replace("\\", "\\\\").replace('"', '\\"')


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.+?)\n---\s*\n", re.DOTALL)

_TEMPLATE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "article": ("title", "author"),
    "report": ("title", "author"),
}
_DEFAULT_REQUIRED_FIELDS: tuple[str, ...] = ("title",)


def _parse_frontmatter(md_content: str) -> dict[str, str]:
    """Extract YAML-like frontmatter from markdown content.

    Supports simple key: value pairs (no nested YAML).
    Returns a dict of string keys to string values.
    """
    match = _FRONTMATTER_RE.match(md_content)
    if not match:
        return {}

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sep = line.find(":")
        if sep == -1:
            continue
        key = line[:sep].strip().lower()
        value = line[sep + 1 :].strip().strip("\"'")
        if key and value:
            metadata[key] = value
    return metadata


def _strip_frontmatter_body(md_content: str) -> str:
    """Return the body portion of markdown content, stripping any frontmatter."""
    match = _FRONTMATTER_RE.match(md_content)
    return md_content[match.end() :] if match else md_content


def _extract_single_h1(body: str) -> tuple[str | None, str]:
    """Extract title from a single H1 heading and promote remaining headings.

    When exactly one H1 exists (outside code blocks), removes it and reduces
    all other heading levels by one (## -> #, ### -> ##, etc.).
    Returns (extracted_title, modified_body).
    """
    lines = body.split("\n")
    h1_indices: list[int] = []
    in_code_block = False

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block and re.match(r"^# (?!#)", line):
            h1_indices.append(i)

    if len(h1_indices) != 1:
        return None, body

    title = re.sub(r"^# +", "", lines[h1_indices[0]]).strip()

    result: list[str] = []
    in_code_block = False
    for i, line in enumerate(lines):
        if i == h1_indices[0]:
            continue
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
        if not in_code_block and re.match(r"^#{2,} ", line):
            line = line[1:]  # remove one '#' to promote
        result.append(line)

    return title, "\n".join(result)


def _build_frontmatter_block(metadata: dict[str, str]) -> str:
    """Build a YAML frontmatter block string from a metadata dict."""
    lines = ["---"]
    for key, value in metadata.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _update_file_frontmatter(
    md_file: Path, md_content: str, metadata: dict[str, str]
) -> str:
    """Write updated frontmatter to the source file. Returns new file content."""
    match = _FRONTMATTER_RE.match(md_content)
    fm_block = _build_frontmatter_block(metadata)
    if match:
        new_content = fm_block + md_content[match.end() :]
    else:
        new_content = fm_block + "\n" + md_content
    md_file.write_text(new_content, encoding="utf-8")
    return new_content


def _ensure_frontmatter(
    md_file: Path,
    md_content: str,
    frontmatter: dict[str, str],
    template_name: str,
) -> tuple[str, dict[str, str]]:
    """Prompt for missing required frontmatter fields and update the source file.

    Returns (updated_content, updated_frontmatter).
    """
    from rich.prompt import Prompt

    required = _TEMPLATE_REQUIRED_FIELDS.get(
        template_name, _DEFAULT_REQUIRED_FIELDS
    )
    missing = [f for f in required if f not in frontmatter]

    if not missing:
        return md_content, frontmatter

    if not is_interactive():
        names = ", ".join(missing)
        err_console.print(
            f"[yellow]Warning:[/yellow] Missing frontmatter: {names}. "
            "Run interactively to be prompted, or add to file."
        )
        return md_content, frontmatter

    err_console.print(
        f"[yellow]Missing frontmatter for {template_name}:[/yellow] "
        + ", ".join(missing)
    )

    updated = dict(frontmatter)
    for field in missing:
        value = Prompt.ask(f"  {field.capitalize()}", console=err_console)
        if value.strip():
            updated[field] = value.strip()

    new_content = _update_file_frontmatter(md_file, md_content, updated)
    return new_content, updated


def _wrap_md_with_template(
    md_file: Path,
    template_dir: Path,
    *,
    frontmatter: dict[str, str] | None = None,
) -> str:
    """Generate a .typ file that imports the template and renders markdown."""
    md_abs = md_file.resolve().as_posix()
    if frontmatter is None:
        md_content = md_file.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(md_content)

    brand_toml = brand_install_dir() / "brand.toml"
    brand = load_brand_colors(brand_toml)

    brand_vars = f'#let company-name = "{_escape_typst_string(brand.company_name)}"\n'
    if brand.company_tagline:
        brand_vars += f'#let company-tagline = "{_escape_typst_string(brand.company_tagline)}"\n'
    if brand.primary:
        brand_vars += f'#let primary-color = rgb("{_escape_typst_string(brand.primary)}")\n'
    if brand.secondary:
        brand_vars += f'#let secondary-color = rgb("{_escape_typst_string(brand.secondary)}")\n'

    lib_path = (template_dir / "lib.typ").as_posix()

    # Build template() call with frontmatter metadata
    template_args = ["company-name: company-name"]
    for key in ("title", "subtitle", "author", "organization", "date", "version"):
        if key in frontmatter:
            template_args.append(
                f'{key}: "{_escape_typst_string(frontmatter[key])}"'
            )
    args_str = ", ".join(template_args)

    # Strip frontmatter so cmarker doesn't render it as content
    strip_fm = ""
    if frontmatter:
        strip_fm = (
            '#let _strip-frontmatter(s) = {\n'
            '  let m = s.match(regex("(?s)\\\\A---\\\\s*\\\\n.+?\\\\n---\\\\s*\\\\n"))\n'
            '  if m != none { s.slice(m.end) } else { s }\n'
            '}\n'
        )
        read_expr = f'_strip-frontmatter(read("{md_abs}"))'
    else:
        read_expr = f'read("{md_abs}")'

    # Slides template uses render-slides() instead of show/cmarker pattern
    is_slides = template_dir.name == "slides"

    if is_slides:
        return (
            f'#import "{lib_path}": *\n'
            f"\n"
            f"{brand_vars}"
            f"{strip_fm}"
            f"\n"
            f"#render-slides({read_expr}, {args_str})\n"
        )

    return (
        f'#import "{lib_path}": *\n'
        f"\n"
        f"{brand_vars}"
        f"{strip_fm}"
        f"\n"
        f"#show: doc => template(doc, {args_str})\n"
        f"\n"
        f'#{{  import "{_CMARKER_PACKAGE}"\n'
        f"   cmarker.render({read_expr}, smart-punctuation: true, scope: (image: (source, alt: none, format: auto) => image(source, alt: alt, format: format)))\n"
        f"}}\n"
    )


def _wrap_md_plain(md_file: Path) -> str:
    """Generate a .typ file that renders plain markdown (no template)."""
    md_abs = md_file.resolve().as_posix()
    return (
        f'#{{  import "{_CMARKER_PACKAGE}"\n'
        f'   cmarker.render(read("{md_abs}"), smart-punctuation: true, scope: (image: (source, alt: none, format: auto) => image(source, alt: alt, format: format)))\n'
        f"}}\n"
    )
