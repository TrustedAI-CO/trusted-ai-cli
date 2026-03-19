"""Tests for tai.core.typst — binary detection, version check, compilation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tai.core.errors import TypstCompileError, TypstNotFoundError, TypstVersionError
from tai.core.typst import (
    check_version,
    compile_document,
    find_typst,
    parse_version,
)


# ── find_typst ───────────────────────────────────────────────────────────────


class TestFindTypst:
    def test_found(self) -> None:
        with patch("shutil.which", return_value="/usr/local/bin/typst"):
            result = find_typst()
        assert result == Path("/usr/local/bin/typst")

    def test_not_found(self) -> None:
        with patch("shutil.which", return_value=None):
            with pytest.raises(TypstNotFoundError):
                find_typst()


# ── parse_version ────────────────────────────────────────────────────────────


class TestParseVersion:
    def test_standard_output(self) -> None:
        assert parse_version("typst 0.12.0 (abcdef1)") == "0.12.0"

    def test_version_only(self) -> None:
        assert parse_version("0.13.1") == "0.13.1"

    def test_no_version(self) -> None:
        assert parse_version("unknown") == "0.0.0"

    def test_multiline(self) -> None:
        assert parse_version("typst 0.14.0\nsome other line") == "0.14.0"


# ── check_version ────────────────────────────────────────────────────────────


class TestCheckVersion:
    def test_version_ok(self) -> None:
        mock_result = MagicMock(stdout="typst 0.13.0 (abc)")
        with patch("subprocess.run", return_value=mock_result):
            version = check_version(Path("/usr/local/bin/typst"), "0.12.0")
        assert version == "0.13.0"

    def test_version_too_old(self) -> None:
        mock_result = MagicMock(stdout="typst 0.10.0 (abc)")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(TypstVersionError):
                check_version(Path("/usr/local/bin/typst"), "0.12.0")

    def test_exact_minimum(self) -> None:
        mock_result = MagicMock(stdout="typst 0.12.0 (abc)")
        with patch("subprocess.run", return_value=mock_result):
            version = check_version(Path("/usr/local/bin/typst"), "0.12.0")
        assert version == "0.12.0"


# ── compile ──────────────────────────────────────────────────────────────────


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

    def test_failure(self, tmp_path: Path) -> None:
        input_file = tmp_path / "bad.typ"
        output_file = tmp_path / "bad.pdf"
        input_file.write_text("bad syntax")

        mock_result = MagicMock(returncode=1, stderr="error: unexpected token")
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(TypstCompileError):
                compile_document(Path("/usr/local/bin/typst"), input_file, output_file)

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

    def test_timeout_raises(self, tmp_path: Path) -> None:
        input_file = tmp_path / "doc.typ"
        output_file = tmp_path / "doc.pdf"
        input_file.write_text("Hello")

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("typst", 120)):
            with pytest.raises(TypstCompileError):
                compile_document(Path("/usr/local/bin/typst"), input_file, output_file)

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        input_file = tmp_path / "doc.typ"
        output_file = tmp_path / "doc.pdf"
        input_file.write_text("Hello")

        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(TypstNotFoundError):
                compile_document(Path("/usr/local/bin/typst"), input_file, output_file)
