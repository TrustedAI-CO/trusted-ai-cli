"""Tests for tai.core.typst — binary detection, version checking, compilation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tai.core.errors import (
    TypstCompileError,
    TypstError,
    TypstNotFoundError,
    TypstVersionError,
)
from tai.core.typst import (
    CompileResult,
    MIN_TYPST_VERSION,
    _version_tuple,
    check_version,
    compile_document,
    find_typst,
    parse_version,
)


# ── parse_version ──────────────────────────────────────────────────────


class TestParseVersion:
    def test_standard_output(self) -> None:
        assert parse_version("typst 0.12.0 (abcdef)") == "0.12.0"

    def test_version_only(self) -> None:
        assert parse_version("0.13.1") == "0.13.1"

    def test_no_version(self) -> None:
        assert parse_version("unknown output") == "0.0.0"

    def test_multiline(self) -> None:
        assert parse_version("typst 0.12.0\nsome other line") == "0.12.0"


# ── _version_tuple ─────────────────────────────────────────────────────


class TestVersionTuple:
    def test_basic(self) -> None:
        assert _version_tuple("0.12.0") == (0, 12, 0)

    def test_comparison(self) -> None:
        assert _version_tuple("0.12.0") >= _version_tuple("0.12.0")
        assert _version_tuple("0.13.0") > _version_tuple("0.12.0")
        assert _version_tuple("0.11.9") < _version_tuple("0.12.0")


# ── find_typst ─────────────────────────────────────────────────────────


class TestFindTypst:
    def test_found(self) -> None:
        with patch("shutil.which", return_value="/usr/local/bin/typst"):
            result = find_typst()
            assert result == Path("/usr/local/bin/typst")

    def test_not_found(self) -> None:
        with patch("shutil.which", return_value=None):
            with pytest.raises(TypstNotFoundError):
                find_typst()


# ── check_version ──────────────────────────────────────────────────────


class TestCheckVersion:
    def test_version_ok(self) -> None:
        mock_result = MagicMock(stdout="typst 0.12.0 (abcdef)", returncode=0)
        with patch("subprocess.run", return_value=mock_result):
            version = check_version(Path("/usr/local/bin/typst"))
            assert version == "0.12.0"

    def test_version_too_old(self) -> None:
        mock_result = MagicMock(stdout="typst 0.11.0", returncode=0)
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(TypstVersionError):
                check_version(Path("/usr/local/bin/typst"))

    def test_exact_minimum(self) -> None:
        mock_result = MagicMock(stdout="typst 0.12.0 (abc)", returncode=0)
        with patch("subprocess.run", return_value=mock_result):
            version = check_version(Path("/usr/local/bin/typst"), "0.12.0")
            assert version == "0.12.0"

    def test_binary_disappeared(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(TypstNotFoundError):
                check_version(Path("/gone/typst"))

    def test_timeout(self) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("typst", 10)):
            with pytest.raises(TypstError, match="timed out"):
                check_version(Path("/usr/local/bin/typst"))


# ── compile_document ───────────────────────────────────────────────────


class TestCompileDocument:
    def test_success(self, tmp_path: Path) -> None:
        input_file = tmp_path / "doc.typ"
        output_file = tmp_path / "doc.pdf"
        input_file.write_text("Hello")

        mock_result = MagicMock(returncode=0, stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = compile_document(Path("/usr/local/bin/typst"), input_file, output_file)

        assert result.output_path == output_file
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "/usr/local/bin/typst"
        assert cmd[1] == "compile"
        assert "--root" not in cmd

    def test_with_root(self, tmp_path: Path) -> None:
        input_file = tmp_path / "doc.typ"
        output_file = tmp_path / "doc.pdf"
        input_file.write_text("Hello")

        mock_result = MagicMock(returncode=0, stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            compile_document(
                Path("/usr/local/bin/typst"),
                input_file,
                output_file,
                root=tmp_path,
            )

        cmd = mock_run.call_args[0][0]
        assert "--root" in cmd
        assert str(tmp_path) in cmd

    def test_compile_error(self, tmp_path: Path) -> None:
        input_file = tmp_path / "bad.typ"
        output_file = tmp_path / "bad.pdf"
        input_file.write_text("bad syntax")

        mock_result = MagicMock(returncode=1, stderr="error: unexpected token")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(TypstCompileError):
                compile_document(Path("/usr/local/bin/typst"), input_file, output_file)

    def test_timeout(self, tmp_path: Path) -> None:
        input_file = tmp_path / "doc.typ"
        output_file = tmp_path / "doc.pdf"
        input_file.write_text("Hello")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("typst", 120)):
            with pytest.raises(TypstCompileError) as exc_info:
                compile_document(Path("/usr/local/bin/typst"), input_file, output_file)
            assert "timed out" in exc_info.value.hint

    def test_binary_missing(self, tmp_path: Path) -> None:
        input_file = tmp_path / "doc.typ"
        output_file = tmp_path / "doc.pdf"
        input_file.write_text("Hello")

        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(TypstNotFoundError):
                compile_document(Path("/usr/local/bin/typst"), input_file, output_file)
