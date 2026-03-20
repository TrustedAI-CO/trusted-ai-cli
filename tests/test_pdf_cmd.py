"""Tests for tai.commands.pdf — frontmatter parsing, escaping, wrapper generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from tai.commands.pdf import (
    _build_frontmatter_block,
    _ensure_frontmatter,
    _escape_typst_string,
    _extract_single_h1,
    _parse_frontmatter,
    _strip_frontmatter_body,
    _update_file_frontmatter,
    _wrap_md_plain,
)


# ── _parse_frontmatter ─────────────────────────────────────────────────


class TestParseFrontmatter:
    def test_full_frontmatter(self):
        md = "---\ntitle: My Title\nauthor: Tran Thien\ndate: March 19, 2026\n---\n\n# Body"
        result = _parse_frontmatter(md)
        assert result["title"] == "My Title"
        assert result["author"] == "Tran Thien"
        assert result["date"] == "March 19, 2026"

    def test_no_frontmatter(self):
        assert _parse_frontmatter("# Just a heading\n\nSome text.") == {}

    def test_empty_string(self):
        assert _parse_frontmatter("") == {}

    def test_quoted_values(self):
        md = '---\ntitle: "Quoted Title"\nauthor: \'Single Quoted\'\n---\n'
        result = _parse_frontmatter(md)
        assert result["title"] == "Quoted Title"
        assert result["author"] == "Single Quoted"

    def test_unicode_values(self):
        md = "---\ntitle: 日本語タイトル\nauthor: Trần Thiện\n---\n"
        result = _parse_frontmatter(md)
        assert result["title"] == "日本語タイトル"
        assert result["author"] == "Trần Thiện"

    def test_skips_comments(self):
        md = "---\ntitle: Title\n# this is a comment\nauthor: Author\n---\n"
        result = _parse_frontmatter(md)
        assert "title" in result
        assert "author" in result

    def test_skips_empty_lines(self):
        md = "---\ntitle: Title\n\nauthor: Author\n---\n"
        result = _parse_frontmatter(md)
        assert len(result) == 2

    def test_key_normalization(self):
        md = "---\nTitle: My Title\nAUTHOR: Me\n---\n"
        result = _parse_frontmatter(md)
        assert result["title"] == "My Title"
        assert result["author"] == "Me"

    def test_colon_in_value(self):
        md = "---\ntitle: Time: 10:30 AM\n---\n"
        result = _parse_frontmatter(md)
        assert result["title"] == "Time: 10:30 AM"

    def test_empty_value_skipped(self):
        md = "---\ntitle:\nauthor: Me\n---\n"
        result = _parse_frontmatter(md)
        assert "title" not in result
        assert result["author"] == "Me"


# ── _escape_typst_string ──────────────────────────────────────────────


class TestEscapeTypstString:
    def test_no_special_chars(self):
        assert _escape_typst_string("Hello World") == "Hello World"

    def test_backslash(self):
        assert _escape_typst_string("path\\to\\file") == "path\\\\to\\\\file"

    def test_double_quote(self):
        assert _escape_typst_string('say "hello"') == 'say \\"hello\\"'

    def test_combined(self):
        assert _escape_typst_string('a\\b"c') == 'a\\\\b\\"c'

    def test_unicode_passthrough(self):
        assert _escape_typst_string("日本語") == "日本語"

    def test_typst_markup_safe_in_strings(self):
        """Typst markup chars (#, $, @) are NOT interpreted inside string literals."""
        assert _escape_typst_string("Cost $50") == "Cost $50"
        assert _escape_typst_string("#hashtag") == "#hashtag"
        assert _escape_typst_string("@mention") == "@mention"


# ── _wrap_md_plain ─────────────────────────────────────────────────────


# ── _strip_frontmatter_body ───────────────────────────────────────────


class TestStripFrontmatterBody:
    def test_strips_frontmatter(self):
        md = "---\ntitle: T\n---\n\nBody text"
        result = _strip_frontmatter_body(md)
        assert result.strip() == "Body text"

    def test_no_frontmatter_returns_all(self):
        md = "# Heading\n\nBody"
        assert _strip_frontmatter_body(md) == md


# ── _extract_single_h1 ───────────────────────────────────────────────


class TestExtractSingleH1:
    def test_single_h1_extracted(self):
        body = "\n# My Title\n\n## Section 1\n\nText\n\n### Subsection\n"
        title, promoted = _extract_single_h1(body)
        assert title == "My Title"
        assert "# Section 1" in promoted
        assert "## Subsection" in promoted
        assert "# My Title" not in promoted

    def test_no_h1_returns_none(self):
        body = "## Section\n\nText"
        title, result = _extract_single_h1(body)
        assert title is None
        assert result == body

    def test_multiple_h1_returns_none(self):
        body = "# First\n\n# Second\n"
        title, result = _extract_single_h1(body)
        assert title is None
        assert result == body

    def test_h1_inside_code_block_ignored(self):
        body = "# Real Title\n\n```\n# Not a heading\n```\n\n## Section\n"
        title, promoted = _extract_single_h1(body)
        assert title == "Real Title"
        assert "# Not a heading" in promoted  # unchanged inside code block
        assert "# Section" in promoted  # promoted from ##

    def test_heading_promotion_depth(self):
        body = "# Title\n\n## H2\n\n### H3\n\n#### H4\n"
        title, promoted = _extract_single_h1(body)
        assert title == "Title"
        assert "# H2" in promoted
        assert "## H3" in promoted
        assert "### H4" in promoted

    def test_empty_body(self):
        title, result = _extract_single_h1("")
        assert title is None
        assert result == ""


# ── _build_frontmatter_block ─────────────────────────────────────────


class TestBuildFrontmatterBlock:
    def test_builds_valid_block(self):
        result = _build_frontmatter_block({"title": "T", "author": "A"})
        assert result == "---\ntitle: T\nauthor: A\n---\n"

    def test_empty_metadata(self):
        result = _build_frontmatter_block({})
        assert result == "---\n---\n"


# ── _update_file_frontmatter ─────────────────────────────────────────


class TestUpdateFileFrontmatter:
    def test_adds_frontmatter_to_plain_md(self, tmp_path: Path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n\nWorld")
        content = md_file.read_text()
        new_content = _update_file_frontmatter(
            md_file, content, {"title": "Hello"}
        )
        assert new_content.startswith("---\ntitle: Hello\n---\n")
        assert "# Hello" in new_content
        assert md_file.read_text() == new_content

    def test_replaces_existing_frontmatter(self, tmp_path: Path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: Old\n---\n\nBody")
        content = md_file.read_text()
        new_content = _update_file_frontmatter(
            md_file, content, {"title": "New", "author": "Me"}
        )
        assert "title: New" in new_content
        assert "author: Me" in new_content
        assert "title: Old" not in new_content
        assert "\nBody" in new_content


# ── _ensure_frontmatter ──────────────────────────────────────────────


class TestEnsureFrontmatter:
    def test_no_missing_fields_returns_unchanged(self, tmp_path: Path):
        md_file = tmp_path / "test.md"
        md_file.write_text("---\ntitle: T\nauthor: A\n---\n\nBody")
        content = md_file.read_text()
        fm = {"title": "T", "author": "A"}
        new_content, new_fm = _ensure_frontmatter(
            md_file, content, fm, "article"
        )
        assert new_content == content
        assert new_fm == fm

    def test_non_interactive_warns(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("tai.commands.pdf.is_interactive", lambda: False)
        md_file = tmp_path / "test.md"
        md_file.write_text("Body only")
        content = md_file.read_text()
        new_content, new_fm = _ensure_frontmatter(
            md_file, content, {}, "article"
        )
        assert new_content == content  # unchanged
        assert new_fm == {}


# ── _wrap_md_plain ─────────────────────────────────────────────────────


class TestWrapMdPlain:
    def test_generates_valid_typst(self, tmp_path: Path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n\nWorld")
        result = _wrap_md_plain(md_file)
        assert "cmarker" in result
        assert str(md_file.resolve().as_posix()) in result
        assert "smart-punctuation: true" in result
