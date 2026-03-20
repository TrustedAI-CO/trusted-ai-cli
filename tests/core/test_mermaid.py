"""Tests for tai.core.mermaid — local mermaid diagram rendering."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tai.core.config import BrandColors
from tai.core.errors import MermaidError
from tai.core.mermaid import (
    _build_mmdc_config,
    _content_hash,
    _find_mmdc,
    _parse_caption,
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


class TestBuildMmdcConfig:
    def test_no_brand(self) -> None:
        assert _build_mmdc_config(None) is None

    def test_no_primary(self) -> None:
        assert _build_mmdc_config(BrandColors()) is None

    def test_primary_only(self) -> None:
        config = _build_mmdc_config(BrandColors(primary="#1a73e8"))
        assert config == {
            "theme": "base",
            "themeVariables": {"primaryColor": "#1a73e8"},
        }

    def test_primary_and_secondary(self) -> None:
        config = _build_mmdc_config(
            BrandColors(primary="#1a73e8", secondary="#4a4a4a")
        )
        assert config == {
            "theme": "base",
            "themeVariables": {
                "primaryColor": "#1a73e8",
                "secondaryColor": "#4a4a4a",
            },
        }


class TestFindMmdc:
    def test_found(self) -> None:
        with patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"):
            assert _find_mmdc() == "/usr/bin/mmdc"

    def test_not_found_raises(self) -> None:
        with patch("tai.core.mermaid.shutil.which", return_value=None):
            with pytest.raises(MermaidError, match="not installed"):
                _find_mmdc()


# ── helper to mock successful mmdc rendering ─────────────────────────────────


def _mock_mmdc_success(svg_content: bytes = b"<svg>test</svg>"):
    """Return a side_effect function that writes SVG to the output path."""

    def side_effect(cmd, **kwargs):
        output_idx = cmd.index("-o") + 1
        output_path = Path(cmd[output_idx])
        output_path.write_bytes(svg_content)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    return side_effect


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

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ),
        ):
            result = preprocess(content, cache_base=tmp_path)

        assert "```mermaid" not in result.content
        assert "TAIMERMAID0" in result.content
        assert result.has_diagrams
        assert len(result.diagrams) == 1

        cached_files = list(tmp_path.glob("*.svg"))
        assert len(cached_files) == 1
        assert cached_files[0].read_bytes() == b"<svg>test</svg>"

    def test_single_block_cache_hit(self, tmp_path: Path) -> None:
        source = "graph TD\n  A --> B\n"
        content = f"# Title\n\n```mermaid\n{source}```\n"

        cache_file = tmp_path / f"{_content_hash(source)}.svg"
        cache_file.write_bytes(b"<svg>cached</svg>")

        with patch("tai.core.mermaid.subprocess.run") as mock_run:
            result = preprocess(content, cache_base=tmp_path)

        mock_run.assert_not_called()
        assert result.has_diagrams
        assert result.diagrams[0].svg_path == cache_file

    def test_multiple_blocks_parallel(self, tmp_path: Path) -> None:
        content = (
            "```mermaid\ngraph TD\n  A --> B\n```\n\n"
            "Some text\n\n"
            "```mermaid\nsequenceDiagram\n  A->>B: Hello\n```\n"
        )

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ),
        ):
            result = preprocess(content, cache_base=tmp_path)

        assert len(result.diagrams) == 2
        assert "TAIMERMAID0" in result.content
        assert "TAIMERMAID1" in result.content
        assert "```mermaid" not in result.content

    def test_caption_parsing(self, tmp_path: Path) -> None:
        content = "```mermaid\n%% caption: System Flow\ngraph TD\n  A --> B\n```\n"

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ),
        ):
            result = preprocess(content, cache_base=tmp_path)

        assert result.diagrams[0].caption == "System Flow"

    def test_brand_colors_passed(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"
        brand = BrandColors(primary="#ff0000")

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ) as mock_run,
        ):
            preprocess(content, brand=brand, cache_base=tmp_path)

        cmd = mock_run.call_args[0][0]
        assert "--configFile" in cmd

    def test_fails_when_mmdc_missing(self, tmp_path: Path) -> None:
        content = "# Title\n\n```mermaid\ngraph TD\n  A --> B\n```\n\nMore text."

        with patch("tai.core.mermaid.shutil.which", return_value=None):
            with pytest.raises(MermaidError, match="not installed"):
                preprocess(content, cache_base=tmp_path)

    def test_no_brand_no_config(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ) as mock_run,
        ):
            preprocess(content, brand=None, cache_base=tmp_path)

        cmd = mock_run.call_args[0][0]
        assert "--configFile" not in cmd


# ── typst show rules tests ──────────────────────────────────────────────────


class TestTypstShowRules:
    def test_generates_image_rule(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ),
        ):
            result = preprocess(content, cache_base=tmp_path)

        rules = result.typst_show_rules()
        assert 'show regex("TAIMERMAID0")' in rules
        assert "image(" in rules
        assert ".svg" in rules
        assert 'fit: "contain"' in rules
        assert "height: 50%" in rules

    def test_generates_figure_rule_with_caption(self, tmp_path: Path) -> None:
        content = "```mermaid\n%% caption: My Flow\ngraph TD\n  A --> B\n```\n"

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ),
        ):
            result = preprocess(content, cache_base=tmp_path)

        rules = result.typst_show_rules()
        assert "figure(" in rules
        assert "My Flow" in rules

    def test_no_rules_without_diagrams(self) -> None:
        result = preprocess("# No mermaid here")
        assert result.typst_show_rules() == ""


# ── error handling tests ─────────────────────────────────────────────────────


class TestPreprocessErrors:
    def test_mmdc_nonzero_exit(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        mock_result = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="Parse error"
        )
        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch("tai.core.mermaid.subprocess.run", return_value=mock_result),
        ):
            with pytest.raises(MermaidError, match="diagram #1 failed"):
                preprocess(content, cache_base=tmp_path)

    def test_mmdc_timeout(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="mmdc", timeout=60),
            ),
        ):
            with pytest.raises(MermaidError, match="timed out"):
                preprocess(content, cache_base=tmp_path)

    def test_mmdc_not_found_at_runtime(self, tmp_path: Path) -> None:
        """mmdc found by shutil.which but missing when subprocess runs."""
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=FileNotFoundError("mmdc"),
            ),
        ):
            with pytest.raises(MermaidError, match="mmdc.*not found"):
                preprocess(content, cache_base=tmp_path)

    def test_invalid_svg_output(self, tmp_path: Path) -> None:
        content = "```mermaid\ngraph TD\n  A --> B\n```\n"

        def write_bad_svg(cmd, **kwargs):
            output_path = Path(cmd[cmd.index("-o") + 1])
            output_path.write_bytes(b"not an svg at all")
            return subprocess.CompletedProcess(cmd, 0)

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch("tai.core.mermaid.subprocess.run", side_effect=write_bad_svg),
        ):
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

        original_write_bytes = Path.write_bytes

        def selective_write_error(self_path, data):
            # Only fail when writing to the cache dir, allow temp files
            if str(self_path).startswith(str(tmp_path)):
                raise OSError("disk full")
            return original_write_bytes(self_path, data)

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ),
            patch.object(Path, "write_bytes", selective_write_error),
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

        with (
            patch("tai.core.mermaid.shutil.which", return_value="/usr/bin/mmdc"),
            patch(
                "tai.core.mermaid.subprocess.run",
                side_effect=_mock_mmdc_success(),
            ),
        ):
            preprocess(content, cache_base=cache)

        assert cache.is_dir()
