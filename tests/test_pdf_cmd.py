"""Tests for tai.commands.pdf — frontmatter parsing, escaping, wrapper generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from tai.commands.pdf import (
    _parse_frontmatter,
    _escape_typst_string,
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


class TestWrapMdPlain:
    def test_generates_valid_typst(self, tmp_path: Path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n\nWorld")
        result = _wrap_md_plain(md_file)
        assert "cmarker" in result
        assert str(md_file.resolve().as_posix()) in result
        assert "smart-punctuation: true" in result
