"""Mermaid diagram rendering for PDF compilation.

Detects ```mermaid code blocks in markdown, renders them via the
mermaid.ink API to SVG, caches results by content hash, and replaces
blocks with text placeholders. Typst show rules at the document level
then swap placeholders for actual #image() calls.

This two-step approach avoids cmarker's eval scope, which resolves
image paths relative to the cmarker package directory.
"""

from __future__ import annotations

import base64
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from tai.core.config import BrandColors
from tai.core.errors import MermaidError

_MERMAID_INK_BASE = "https://mermaid.ink/svg/"

_MERMAID_BLOCK_RE = re.compile(
    r"```mermaid\s*\n(.*?)```",
    re.DOTALL,
)

_CAPTION_RE = re.compile(r"%%\s*caption:\s*(.+)", re.IGNORECASE)

_PLACEHOLDER_PREFIX = "TAIMERMAID"

_API_TIMEOUT_SECONDS = 30
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


_FOREIGN_OBJECT_RE = re.compile(
    r"<foreignObject[^>]*>(.*?)</foreignObject>",
    re.DOTALL,
)

_HTML_TEXT_RE = re.compile(r"<p>(.*?)</p>", re.DOTALL)

_HTML_TAG_RE = re.compile(r"<[^>]+>")

_FO_DIMENSIONS_RE = re.compile(
    r'width="([^"]*)".*?height="([^"]*)"',
)


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = _HTML_TAG_RE.sub("", html)
    return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()


def _fix_foreign_objects(svg: bytes) -> bytes:
    """Replace <foreignObject> HTML blocks with native SVG <text> elements.

    Typst's SVG renderer doesn't support foreignObject (used by mermaid
    for node labels in flowcharts). This extracts the text content and
    creates a centered <text> element instead.
    """
    svg_str = svg.decode("utf-8")

    def _replace_fo(match: re.Match[str]) -> str:
        fo_content = match.group(1)
        attrs_str = match.group(0).split(">")[0]

        # Extract text from <p> tags
        text_match = _HTML_TEXT_RE.search(fo_content)
        if not text_match:
            return ""
        text = _strip_html_tags(text_match.group(1))
        if not text:
            return ""

        # Extract dimensions for centering
        dim_match = _FO_DIMENSIONS_RE.search(attrs_str)
        if dim_match:
            cx = float(dim_match.group(1)) / 2
            cy = float(dim_match.group(2)) / 2
        else:
            cx, cy = 0, 0

        return (
            f'<text x="{cx}" y="{cy}" '
            f'text-anchor="middle" dominant-baseline="central" '
            f'font-size="14px">{text}</text>'
        )

    result = _FOREIGN_OBJECT_RE.sub(_replace_fo, svg_str)
    return result.encode("utf-8")


def _build_mermaid_ink_url(source: str, brand: BrandColors | None) -> str:
    """Build a mermaid.ink SVG URL with optional brand theme."""
    encoded = base64.urlsafe_b64encode(source.encode("utf-8")).decode("ascii")
    url = f"{_MERMAID_INK_BASE}{encoded}"

    if brand and brand.primary:
        theme_vars = f"primaryColor:{brand.primary}"
        if brand.secondary:
            theme_vars += f",secondaryColor:{brand.secondary}"
        url += f"?theme=base&themeVariables={theme_vars}"

    return url


def _render_single(
    source: str,
    cache: Path,
    brand: BrandColors | None,
    index: int,
) -> Path:
    """Render one mermaid diagram to SVG via mermaid.ink API.

    Returns the path to the cached SVG file.
    """
    content_hash = _content_hash(source)
    cached_path = cache / f"{content_hash}.svg"

    if cached_path.is_file():
        return cached_path

    url = _build_mermaid_ink_url(source, brand)

    try:
        response = httpx.get(url, timeout=_API_TIMEOUT_SECONDS, follow_redirects=True)
    except httpx.TimeoutException as exc:
        raise MermaidError(
            f"Mermaid diagram #{index + 1} timed out after {_API_TIMEOUT_SECONDS}s",
            hint="Check your network connection or simplify the diagram.",
        ) from exc
    except httpx.HTTPError as exc:
        raise MermaidError(
            f"Mermaid diagram #{index + 1} network error: {exc}",
            hint="Check your network connection.",
        ) from exc

    if response.status_code != 200:
        raise MermaidError(
            f"Mermaid diagram #{index + 1} failed (HTTP {response.status_code})",
            hint="Check the diagram syntax. The mermaid.ink API could not render it.",
        )

    svg_data = response.content
    if not svg_data or b"<svg" not in svg_data[:500]:
        raise MermaidError(
            f"Mermaid diagram #{index + 1} returned invalid SVG",
            hint="Check the diagram syntax.",
        )

    # Convert foreignObject HTML to native SVG text for Typst compatibility
    svg_data = _fix_foreign_objects(svg_data)

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

    Renders each mermaid block via the mermaid.ink API, caches the
    resulting SVG by content hash, and substitutes the code block with
    a unique text placeholder.

    Returns a PreprocessResult containing the modified markdown and
    diagram metadata. Use ``result.typst_show_rules()`` to generate
    Typst show rules that swap placeholders for actual images.
    """
    blocks = list(_MERMAID_BLOCK_RE.finditer(md_content))
    if not blocks:
        return PreprocessResult(content=md_content)

    cache = _cache_dir(cache_base)
    sources = [match.group(1) for match in blocks]
    captions = [_parse_caption(src) for src in sources]

    worker_count = min(len(sources), _MAX_PARALLEL_WORKERS)
    svg_paths: dict[int, Path] = {}

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(_render_single, src, cache, brand, i): i
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
