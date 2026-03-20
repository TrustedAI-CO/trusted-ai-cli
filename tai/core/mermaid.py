"""Mermaid diagram rendering for PDF compilation.

Detects ```mermaid code blocks in markdown, renders them locally via
the mermaid CLI (mmdc), caches results by content hash, and replaces
blocks with text placeholders. Typst show rules at the document level
then swap placeholders for actual #image() calls.

This two-step approach avoids cmarker's eval scope, which resolves
image paths relative to the cmarker package directory.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from tai.core.config import BrandColors
from tai.core.errors import MermaidError

_MERMAID_BLOCK_RE = re.compile(
    r"```mermaid\s*\n(.*?)```",
    re.DOTALL,
)

_CAPTION_RE = re.compile(r"%%\s*caption:\s*(.+)", re.IGNORECASE)

_PLACEHOLDER_PREFIX = "TAIMERMAID"

_RENDER_TIMEOUT_SECONDS = 60
_MAX_PARALLEL_WORKERS = 4


@dataclass(frozen=True)
class DiagramResult:
    """A rendered mermaid diagram with its SVG path and optional caption."""

    svg_path: Path
    caption: str | None
    placeholder: str


@dataclass(frozen=True)
class PreprocessResult:
    """Result of mermaid preprocessing."""

    content: str
    diagrams: tuple[DiagramResult, ...] = ()

    @property
    def has_diagrams(self) -> bool:
        return len(self.diagrams) > 0

    def typst_show_rules(self) -> str:
        """Generate Typst show rules that replace placeholders with images."""
        if not self.diagrams:
            return ""

        rules: list[str] = []
        for d in self.diagrams:
            abs_path = d.svg_path.resolve().as_posix()
            escaped_ph = _escape_typst_string(d.placeholder)
            img = f'image("{abs_path}", width: 90%, height: 50%, fit: "contain")'
            if d.caption:
                escaped_cap = _escape_typst_string(d.caption)
                rules.append(
                    f'#show regex("{escaped_ph}"): _ => figure(\n'
                    f'  {img},\n'
                    f'  caption: [{escaped_cap}],\n'
                    f')'
                )
            else:
                rules.append(
                    f'#show regex("{escaped_ph}"): _ => {img}'
                )
        return "\n".join(rules) + "\n"


def _escape_typst_string(value: str) -> str:
    """Escape a string for safe inclusion in a Typst string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _cache_dir(base: Path | None = None) -> Path:
    """Return the mermaid SVG cache directory, creating it if needed."""
    cache = base or (Path.home() / ".tai" / "cache" / "mermaid")
    try:
        cache.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise MermaidError(
            f"Cannot create cache directory: {cache}",
            hint=f"Check permissions on {cache.parent}: {exc}",
        ) from exc
    return cache


def _content_hash(source: str) -> str:
    """SHA-256 hash of diagram source for cache keying."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _parse_caption(source: str) -> str | None:
    """Extract caption from %% caption: comment in mermaid source."""
    match = _CAPTION_RE.search(source)
    return match.group(1).strip() if match else None


def _find_mmdc() -> str:
    """Locate the mmdc executable or raise with install instructions."""
    path = shutil.which("mmdc")
    if path:
        return path
    raise MermaidError(
        "Mermaid CLI (mmdc) is not installed",
        hint="Install it with: npm install -g @mermaid-js/mermaid-cli",
    )


def _build_mmdc_config(brand: BrandColors | None) -> dict | None:
    """Build a mmdc JSON config dict for brand theming."""
    if not brand or not brand.primary:
        return None
    theme_variables: dict[str, str] = {"primaryColor": brand.primary}
    if brand.secondary:
        theme_variables["secondaryColor"] = brand.secondary
    return {"theme": "base", "themeVariables": theme_variables}


def _render_single(
    source: str,
    cache: Path,
    brand: BrandColors | None,
    index: int,
    mmdc: str = "",
) -> Path:
    """Render one mermaid diagram to SVG via local mmdc CLI.

    Returns the path to the cached SVG file.
    """
    content_hash = _content_hash(source)
    cached_path = cache / f"{content_hash}.svg"

    if cached_path.is_file():
        return cached_path

    mmdc_config = _build_mmdc_config(brand)

    with tempfile.TemporaryDirectory(prefix="tai-mermaid-") as tmp_dir:
        tmp = Path(tmp_dir)
        input_path = tmp / "diagram.mmd"
        output_path = tmp / "diagram.svg"
        input_path.write_text(source, encoding="utf-8")

        cmd = [mmdc, "-i", str(input_path), "-o", str(output_path), "-q"]
        if mmdc_config:
            config_path = tmp / "config.json"
            config_path.write_text(
                json.dumps(mmdc_config), encoding="utf-8"
            )
            cmd.extend(["--configFile", str(config_path)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_RENDER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise MermaidError(
                f"Mermaid diagram #{index + 1} timed out after {_RENDER_TIMEOUT_SECONDS}s",
                hint="Simplify the diagram or increase the timeout.",
            ) from exc
        except FileNotFoundError as exc:
            raise MermaidError(
                "Mermaid CLI (mmdc) not found",
                hint="Install it with: npm install -g @mermaid-js/mermaid-cli",
            ) from exc

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise MermaidError(
                f"Mermaid diagram #{index + 1} failed to render",
                hint=stderr or "Check the diagram syntax.",
            )

        if not output_path.is_file():
            raise MermaidError(
                f"Mermaid diagram #{index + 1} produced no output",
                hint="Check the diagram syntax.",
            )

        svg_data = output_path.read_bytes()
        if not svg_data or b"<svg" not in svg_data[:500]:
            raise MermaidError(
                f"Mermaid diagram #{index + 1} returned invalid SVG",
                hint="Check the diagram syntax.",
            )

    try:
        cached_path.write_bytes(svg_data)
    except OSError as exc:
        raise MermaidError(
            f"Cannot write cached SVG: {cached_path}",
            hint=f"Check disk space and permissions: {exc}",
        ) from exc

    return cached_path


def preprocess(
    md_content: str,
    *,
    brand: BrandColors | None = None,
    cache_base: Path | None = None,
) -> PreprocessResult:
    """Replace mermaid code blocks in markdown with text placeholders.

    Renders each mermaid block via the local mmdc CLI, caches the
    resulting SVG by content hash, and substitutes the code block with
    a unique text placeholder.

    Returns a PreprocessResult containing the modified markdown and
    diagram metadata. Use ``result.typst_show_rules()`` to generate
    Typst show rules that swap placeholders for actual images.
    """
    blocks = list(_MERMAID_BLOCK_RE.finditer(md_content))
    if not blocks:
        return PreprocessResult(content=md_content)

    mmdc = _find_mmdc()
    cache = _cache_dir(cache_base)
    sources = [match.group(1) for match in blocks]
    captions = [_parse_caption(src) for src in sources]

    worker_count = min(len(sources), _MAX_PARALLEL_WORKERS)
    svg_paths: dict[int, Path] = {}

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(_render_single, src, cache, brand, i, mmdc): i
            for i, src in enumerate(sources)
        }
        for future in as_completed(futures):
            idx = futures[future]
            svg_paths[idx] = future.result()

    diagrams: list[DiagramResult] = []
    result = md_content
    for i in reversed(range(len(blocks))):
        match = blocks[i]
        placeholder = f"{_PLACEHOLDER_PREFIX}{i}"
        diagrams.insert(
            0,
            DiagramResult(
                svg_path=svg_paths[i],
                caption=captions[i],
                placeholder=placeholder,
            ),
        )
        result = result[: match.start()] + f"\n{placeholder}\n" + result[match.end() :]

    return PreprocessResult(content=result, diagrams=tuple(diagrams))
