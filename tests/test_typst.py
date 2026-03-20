"""Tests for tai.core.typst — binary detection, version checking, compilation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

import pytest

from tai.core.typst import (
    find_typst,
    parse_version,
    check_version,
    compile_document,
    _version_tuple,
    MIN_TYPST_VERSION,
    CompileResult,
)
from tai.core.errors import (
    TypstNotFoundError,
    TypstVersionError,
    TypstCompileError,
    TypstError,
)


# ── parse_version ──────────────────────────────────────────────────────


class TestParseVersion:
    def test_standard_output(self):
        assert parse_version("typst 0.12.0 (abcdef)") == "0.12.0"

    def test_version_only(self):
        assert parse_version("0.13.1") == "0.13.1"

    def test_no_version(self):
        assert parse_version("unknown output") == "0.0.0"

    def test_multiline(self):
        assert parse_version("typst 0.12.0\nsome other line") == "0.12.0"


# ── _version_tuple ─────────────────────────────────────────────────────


class TestVersionTuple:
    def test_basic(self):
        assert _version_tuple("0.12.0") == (0, 12, 0)

    def test_comparison(self):
        assert _version_tuple("0.12.0") >= _version_tuple("0.12.0")
        assert _version_tuple("0.13.0") > _version_tuple("0.12.0")
        assert _version_tuple("0.11.9") < _version_tuple("0.12.0")


# ── find_typst ─────────────────────────────────────────────────────────


class TestFindTypst:
    def test_found(self):
        with patch("shutil.which", return_value="/usr/local/bin/typst"):
            result = find_typst()
            assert result == Path("/usr/local/bin/typst")

    def test_not_found(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(TypstNotFoundError):
                find_typst()


# ── check_version ──────────────────────────────────────────────────────


class TestCheckVersion:
    def test_version_ok(self):
        mock_result = MagicMock(stdout="typst 0.12.0 (abcdef)", returncode=0)
        with patch("subprocess.run", return_value=mock_result):
            version = check_version(Path("/usr/local/bin/typst"))
            assert version == "0.12.0"

    def test_version_too_old(self):
        mock_result = MagicMock(stdout="typst 0.11.0", returncode=0)
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(TypstVersionError):
                check_version(Path("/usr/local/bin/typst"))

    def test_binary_disappeared(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(TypstNotFoundError):
                check_version(Path("/gone/typst"))

    def test_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("typst", 10)):
            with pytest.raises(TypstError, match="timed out"):
                check_version(Path("/usr/local/bin/typst"))


# ── compile_document ───────────────────────────────────────────────────


class TestCompileDocument:
    def test_success(self, tmp_path: Path):
        output = tmp_path / "out.pdf"
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = compile_document(
                Path("/usr/local/bin/typst"),
                tmp_path / "input.typ",
                output,
            )
            assert result.output_path == output
            # Verify no --root flag when root is None
            args = mock_run.call_args[0][0]
            assert "--root" not in args

    def test_with_root(self, tmp_path: Path):
        output = tmp_path / "out.pdf"
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            compile_document(
                Path("/usr/local/bin/typst"),
                tmp_path / "input.typ",
                output,
                root=Path("/"),
            )
            args = mock_run.call_args[0][0]
            assert "--root" in args
            assert "/" in args

    def test_compile_error(self, tmp_path: Path):
        mock_result = MagicMock(returncode=1, stderr="error: unexpected token")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(TypstCompileError):
                compile_document(
                    Path("/usr/local/bin/typst"),
                    tmp_path / "input.typ",
                    tmp_path / "out.pdf",
                )

    def test_timeout(self, tmp_path: Path):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("typst", 120)):
            with pytest.raises(TypstCompileError) as exc_info:
                compile_document(
                    Path("/usr/local/bin/typst"),
                    tmp_path / "input.typ",
                    tmp_path / "out.pdf",
                )
            assert "timed out" in exc_info.value.hint

    def test_binary_missing(self, tmp_path: Path):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(TypstNotFoundError):
                compile_document(
                    Path("/usr/local/bin/typst"),
                    tmp_path / "input.typ",
                    tmp_path / "out.pdf",
                )
