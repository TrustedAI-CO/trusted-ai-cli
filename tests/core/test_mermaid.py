"""Tests for tai.core.mermaid — mermaid diagram rendering."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from tai.core.config import BrandColors
from tai.core.errors import MermaidError
from tai.core.mermaid import (
    _build_mermaid_ink_url,
    _content_hash,
    _fix_foreign_objects,
    _parse_caption,
    _strip_html_tags,
    preprocess,
)


# ── unit tests: helpers ──────────────────────────────────────────────────────


class TestContentHash:
    def test_deterministic(self) -> None:
        assert _content_hash("graph TD") == _content_hash("graph TD")

    def test_different_input(self) -> None:
        assert _content_hash("graph TD") != _content_hash("graph LR")


class TestParseCaption:
    def test_caption_found(self) -> None:
        source = "%% caption: My Diagram\ngraph TD\n  A --> B"
        assert _parse_caption(source) == "My Diagram"

    def test_caption_case_insensitive(self) -> None:
        assert _parse_caption("%% Caption: Test") == "Test"

    def test_no_caption(self) -> None:
        assert _parse_caption("graph TD\n  A --> B") is None

    def test_caption_strips_whitespace(self) -> None:
        assert _parse_caption("%%   caption:   Trimmed  ") == "Trimmed"


class TestBuildMermaidInkUrl:
    def test_basic_url(self) -> None:
        url = _build_mermaid_ink_url("graph TD", brand=None)
        assert url.startswith("https://mermaid.ink/svg/")
        assert "theme" not in url

    def test_brand_colors(self) -> None:
        brand = BrandColors(primary="#1a73e8", secondary="#4a4a4a")
        url = _build_mermaid_ink_url("graph TD", brand=brand)
        assert "theme=base" in url
        assert "primaryColor:#1a73e8" in url
        assert "secondaryColor:#4a4a4a" in url

    def test_brand_primary_only(self) -> None:
        brand = BrandColors(primary="#1a73e8")
        url = _build_mermaid_ink_url("graph TD", brand=brand)
        assert "primaryColor:#1a73e8" in url
        assert "secondaryColor" not in url

    def test_no_brand_primary(self) -> None:
        brand = BrandColors()
        url = _build_mermaid_ink_url("graph TD", brand=brand)
        assert "theme" not in url


# ── SVG post-processing tests ────────────────────────────────────────────────


class TestStripHtmlTags:
    def test_simple_html(self) -> None:
        assert _strip_html_tags("<p>Hello</p>") == "Hello"

    def test_nested_tags(self) -> None:
        assert _strip_html_tags('<span class="x"><p>World</p></span>') == "World"

    def test_entities(self) -> None:
        assert _strip_html_tags("A &amp; B &lt; C") == "A & B < C"

    def test_empty(self) -> None:
        assert _strip_html_tags("") == ""


class TestFixForeignObjects:
    def test_replaces_foreign_object_with_text(self) -> None:
        svg = (
            b'<svg><g><foreignObject width="80" height="24">'
            b'<div xmlns="http://www.w3.org/1999/xhtml">'
            b'<span class="nodeLabel"><p>User</p></span>'
            b'</div></foreignObject></g></svg>'
        )
        result = _fix_foreign_objects(svg)
        decoded = result.decode("utf-8")
        assert "foreignObject" not in decoded
        assert "<text" in decoded
        assert "User" in decoded
        assert 'text-anchor="middle"' in decoded

    def test_preserves_svg_without_foreign_objects(self) -> None:
        svg = b'<svg><text>Hello</text></svg>'
        result = _fix_foreign_objects(svg)
        assert result == svg

    def test_handles_multiple_foreign_objects(self) -> None:
        svg = (
            b'<svg>'
            b'<foreignObject width="40" height="20">'
            b'<div xmlns="http://www.w3.org/1999/xhtml"><p>A</p></div>'
            b'</foreignObject>'
            b'<foreignObject width="60" height="20">'
            b'<div xmlns="http://www.w3.org/1999/xhtml"><p>B</p></div>'
            b'</foreignObject>'
            b'</svg>'
        )
        result = _fix_foreign_objects(svg).decode("utf-8")
        assert "foreignObject" not in result
        assert ">A<" in result
        assert ">B<" in result

    def test_empty_paragraph_removed(self) -> None:
        svg = (
            b'<foreignObject width="40" height="20">'
            b'<div xmlns="http://www.w3.org/1999/xhtml"><p></p></div>'
            b'</foreignObject>'
        )
        result = _fix_foreign_objects(svg).decode("utf-8")
        assert "foreignObject" not in result
        assert "<text" not in result

    def test_integration_with_preprocess(self, tmp_path: Path) -> None:
        """SVG with foreignObject is post-processed when cached."""
        content = "```mermaid\ngraph TD\n  A[Hello] --> B[World]\n```\n"
        svg_with_fo = (
            b'<svg><foreignObject width="80" height="24">'
            b'<div xmlns="http://www.w3.org/1999/xhtml">'
            b'<span><p>Hello</p></span>'
            b'</div></foreignObject></svg>'
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = svg_with_fo

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            preprocess(content, cache_base=tmp_path)

        # Verify cached file has text elements, not foreignObject
        cached = list(tmp_path.glob("*.svg"))
        assert len(cached) == 1
        cached_content = cached[0].read_text()
        assert "foreignObject" not in cached_content
        assert "Hello" in cached_content


# ── preprocess tests ─────────────────────────────────────────────────────────


class TestPreprocess:
    def test_no_mermaid_blocks(self) -> None:
        content = "# Hello\n\nSome regular markdown."
        result = preprocess(content)
        assert result.content == content
        assert not result.has_diagrams
        assert result.typst_show_rules() == ""

    def test_single_block_cache_miss(self, tmp_path: Path) -> None:
        content = "# Title\n\n```mermaid\ngraph TD\n  A --> B\n```\n\nMore text."
        svg_content = b"<svg>test</svg>"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = svg_content

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            result = preprocess(content, cache_base=tmp_path)

        assert "```mermaid" not in result.content
        assert "TAIMERMAID0" in result.content
        assert result.has_diagrams
        assert len(result.diagrams) == 1

        # Verify SVG was cached
        cached_files = list(tmp_path.glob("*.svg"))
        assert len(cached_files) == 1
        assert cached_files[0].read_bytes() == svg_content

    def test_single_block_cache_hit(self, tmp_path: Path) -> None:
        source = "graph TD\n  A --> B\n"
        content = f"# Title\n\n```mermaid\n{source}```\n"

        # Pre-populate cache
        from tai.core.mermaid import _content_hash

        cache_file = tmp_path / f"{_content_hash(source)}.svg"
        cache_file.write_bytes(b"<svg>cached</svg>")

        with patch("tai.core.mermaid.httpx.get") as mock_get:
            result = preprocess(content, cache_base=tmp_path)

        # API should NOT have been called
        mock_get.assert_not_called()
        assert result.has_diagrams
        assert result.diagrams[0].svg_path == cache_file

    def test_multiple_blocks_parallel(self, tmp_path: Path) -> None:
        content = (
            "```mermaid\ngraph TD\n  A --> B\n```\n\n"
            "Some text\n\n"
            "```mermaid\nsequenceDiagram\n  A->>B: Hello\n```\n"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            result = preprocess(content, cache_base=tmp_path)

        assert len(result.diagrams) == 2
        assert "TAIMERMAID0" in result.content
        assert "TAIMERMAID1" in result.content
        assert "```mermaid" not in result.content

    def test_caption_parsing(self, tmp_path: Path) -> None:
        content = "```mermaid\n%% caption: System Flow\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            result = preprocess(content, cache_base=tmp_path)

        assert result.diagrams[0].caption == "System Flow"

    def test_brand_colors_passed(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"
        brand = BrandColors(primary="#ff0000")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response) as mock_get:
            preprocess(content, brand=brand, cache_base=tmp_path)

        called_url = mock_get.call_args[0][0]
        assert "primaryColor:#ff0000" in called_url

    def test_no_brand_default_theme(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response) as mock_get:
            preprocess(content, brand=None, cache_base=tmp_path)

        called_url = mock_get.call_args[0][0]
        assert "theme" not in called_url


# ── typst show rules tests ──────────────────────────────────────────────────


class TestTypstShowRules:
    def test_generates_image_rule(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            result = preprocess(content, cache_base=tmp_path)

        rules = result.typst_show_rules()
        assert 'show regex("TAIMERMAID0")' in rules
        assert "image(" in rules
        assert ".svg" in rules
        assert 'fit: "contain"' in rules
        assert "height: 50%" in rules

    def test_generates_figure_rule_with_caption(self, tmp_path: Path) -> None:
        content = "```mermaid\n%% caption: My Flow\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            result = preprocess(content, cache_base=tmp_path)

        rules = result.typst_show_rules()
        assert "figure(" in rules
        assert "My Flow" in rules

    def test_no_rules_without_diagrams(self) -> None:
        result = preprocess("# No mermaid here")
        assert result.typst_show_rules() == ""


# ── error handling tests ─────────────────────────────────────────────────────


class TestPreprocessErrors:
    def test_api_error_status(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 400

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            with pytest.raises(MermaidError, match="diagram #1 failed"):
                preprocess(content, cache_base=tmp_path)

    def test_api_timeout(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        with patch(
            "tai.core.mermaid.httpx.get",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(MermaidError, match="timed out"):
                preprocess(content, cache_base=tmp_path)

    def test_api_network_error(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        with patch(
            "tai.core.mermaid.httpx.get",
            side_effect=httpx.ConnectError("refused"),
        ):
            with pytest.raises(MermaidError, match="network error"):
                preprocess(content, cache_base=tmp_path)

    def test_invalid_svg_response(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"not an svg at all"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            with pytest.raises(MermaidError, match="invalid SVG"):
                preprocess(content, cache_base=tmp_path)

    def test_cache_dir_permission_error(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"
        bad_path = tmp_path / "no" / "access"

        with patch("tai.core.mermaid.Path.mkdir", side_effect=OSError("denied")):
            with pytest.raises(MermaidError, match="Cannot create cache"):
                preprocess(content, cache_base=bad_path)

    def test_cache_write_error(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with (
            patch("tai.core.mermaid.httpx.get", return_value=mock_response),
            patch.object(Path, "write_bytes", side_effect=OSError("disk full")),
            patch.object(Path, "is_file", return_value=False),
        ):
            with pytest.raises(MermaidError, match="Cannot write cached SVG"):
                preprocess(content, cache_base=tmp_path)


# ── cache directory tests ────────────────────────────────────────────────────


class TestCacheDir:
    def test_no_cache_dir_without_blocks(self, tmp_path: Path) -> None:
        cache = tmp_path / "new" / "cache"
        preprocess("# No mermaid blocks", cache_base=cache)
        assert not cache.exists()

    def test_creates_cache_dir_on_render(self, tmp_path: Path) -> None:
        cache = tmp_path / "new" / "cache"
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>test</svg>"

        with patch("tai.core.mermaid.httpx.get", return_value=mock_response):
            preprocess(content, cache_base=cache)

        assert cache.is_dir()
