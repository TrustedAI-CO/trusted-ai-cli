"""Tests for tai pdf commands — setup-templates and compile."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from tai.commands.pdf import app

runner = CliRunner()


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def template_source(tmp_path: Path) -> Path:
    """Create a source directory with a valid template."""
    tpl = tmp_path / "source" / "proposal"
    tpl.mkdir(parents=True)
    (tpl / "typst.toml").write_text(
        '[package]\nname = "proposal"\nversion = "0.1.0"\n'
        'description = "Test proposal."\nentrypoint = "lib.typ"\n'
    )
    (tpl / "lib.typ").write_text("#let template(doc) = { doc }\n")
    sub = tpl / "template"
    sub.mkdir()
    (sub / "main.typ").write_text("// main\n")
    return tmp_path / "source"


@pytest.fixture
def install_dir(tmp_path: Path) -> Path:
    """Provide a temp install directory."""
    target = tmp_path / "templates"
    return target


@pytest.fixture
def brand_source(tmp_path: Path) -> Path:
    """Create brand assets source."""
    brand = tmp_path / "brand_src"
    brand.mkdir()
    (brand / "brand.toml").write_text(
        '[company]\nname = "TestCo"\n[colors]\nprimary = "#000"\n'
    )
    return brand


@pytest.fixture
def brand_dir(tmp_path: Path) -> Path:
    """Provide a temp brand directory."""
    return tmp_path / "brand"


@pytest.fixture
def patch_dirs(
    install_dir: Path,
    brand_dir: Path,
    template_source: Path,
    brand_source: Path,
):
    """Patch all directory functions for isolated testing."""
    with (
        patch("tai.commands.pdf.templates_install_dir", return_value=install_dir),
        patch("tai.commands.pdf.brand_install_dir", return_value=brand_dir),
        patch("tai.commands.pdf.find_template_source", return_value=template_source),
        patch("tai.commands.pdf.find_brand_source", return_value=brand_source),
        patch("tai.core.templates.templates_install_dir", return_value=install_dir),
        patch("tai.core.templates.brand_install_dir", return_value=brand_dir),
    ):
        yield


# ── setup-templates tests ───────────────────────────────────────────────────


class TestSetupTemplates:
    def test_happy_path(self, patch_dirs, install_dir: Path) -> None:
        result = runner.invoke(app, ["setup-templates"])
        assert result.exit_code == 0
        assert "proposal" in result.output
        assert (install_dir / "proposal" / "typst.toml").is_file()

    def test_force(self, patch_dirs, install_dir: Path) -> None:
        runner.invoke(app, ["setup-templates"])
        result = runner.invoke(app, ["setup-templates", "--force"])
        assert result.exit_code == 0
        assert "proposal" in result.output

    def test_skip_existing(self, patch_dirs) -> None:
        runner.invoke(app, ["setup-templates"])
        result = runner.invoke(app, ["setup-templates"])
        assert result.exit_code == 0
        assert "exists" in result.output

    def test_list(self, patch_dirs) -> None:
        result = runner.invoke(app, ["setup-templates", "--list"])
        assert result.exit_code == 0
        assert "proposal" in result.output

    def test_list_json(self, patch_dirs) -> None:
        result = runner.invoke(app, ["setup-templates", "--list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "templates" in data
        names = [t["name"] for t in data["templates"]]
        assert "proposal" in names

    def test_remove(self, patch_dirs, install_dir: Path) -> None:
        runner.invoke(app, ["setup-templates"])
        result = runner.invoke(app, ["setup-templates", "--remove"])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_remove_noop(self, patch_dirs) -> None:
        result = runner.invoke(app, ["setup-templates", "--remove"])
        assert result.exit_code == 0
        assert "No installed" in result.output

    def test_json_output(self, patch_dirs) -> None:
        result = runner.invoke(app, ["setup-templates", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "installed" in data
        assert "proposal" in data["installed"]

    def test_source_not_found(self) -> None:
        with (
            patch("tai.commands.pdf.find_template_source", return_value=None),
            patch("tai.commands.pdf.find_brand_source", return_value=None),
        ):
            result = runner.invoke(app, ["setup-templates"])
        assert result.exit_code == 1
        assert "Cannot find" in result.output


# ── compile tests ────────────────────────────────────────────────────────────


class TestCompile:
    def test_no_typst_binary(self) -> None:
        with patch("shutil.which", return_value=None):
            result = runner.invoke(app, ["compile", "test.md"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_file_not_found(self) -> None:
        mock_result = MagicMock(stdout="typst 0.13.0")
        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", return_value=mock_result),
        ):
            result = runner.invoke(app, ["compile", "/nonexistent/file.md"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_compile_typ_happy(self, tmp_path: Path) -> None:
        typ_file = tmp_path / "doc.typ"
        typ_file.write_text("Hello")

        version_result = MagicMock(stdout="typst 0.13.0")
        compile_result = MagicMock(returncode=0, stderr="")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", side_effect=[version_result, compile_result]),
        ):
            result = runner.invoke(app, ["compile", str(typ_file)])
        assert result.exit_code == 0

    def test_compile_md_no_template_warning(self, tmp_path: Path) -> None:
        """When picker returns None, compiles plain markdown with warning."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Hello")

        version_result = MagicMock(stdout="typst 0.13.0")
        compile_result = MagicMock(returncode=0, stderr="")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", side_effect=[version_result, compile_result]),
            patch("tai.commands.pdf._pick_template", return_value=None),
        ):
            result = runner.invoke(app, ["compile", str(md_file)])
        assert result.exit_code == 0
        assert "No --template" in result.output

    def test_compile_md_template_not_found(self, tmp_path: Path) -> None:
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Hello")

        version_result = MagicMock(stdout="typst 0.13.0")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", return_value=version_result),
            patch(
                "tai.commands.pdf.templates_install_dir",
                return_value=tmp_path / "no_templates",
            ),
        ):
            result = runner.invoke(
                app, ["compile", str(md_file), "--template", "missing"]
            )
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_compile_invalid_template_name(self, tmp_path: Path) -> None:
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Hello")

        version_result = MagicMock(stdout="typst 0.13.0")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", return_value=version_result),
        ):
            result = runner.invoke(
                app, ["compile", str(md_file), "--template", "../../etc/passwd"]
            )
        assert result.exit_code == 1
        assert "Invalid template name" in result.output

    def test_compile_empty_md_warning(self, tmp_path: Path) -> None:
        md_file = tmp_path / "empty.md"
        md_file.write_text("")

        version_result = MagicMock(stdout="typst 0.13.0")
        compile_result = MagicMock(returncode=0, stderr="")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", side_effect=[version_result, compile_result]),
            patch("tai.commands.pdf._pick_template", return_value=None),
        ):
            result = runner.invoke(app, ["compile", str(md_file)])
        assert "empty" in result.output

    def test_compile_unsupported_ext(self, tmp_path: Path) -> None:
        txt_file = tmp_path / "doc.txt"
        txt_file.write_text("hello")

        version_result = MagicMock(stdout="typst 0.13.0")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", return_value=version_result),
        ):
            result = runner.invoke(app, ["compile", str(txt_file)])
        assert result.exit_code == 1
        assert "Unsupported" in result.output

    def test_compile_typst_error(self, tmp_path: Path) -> None:
        typ_file = tmp_path / "bad.typ"
        typ_file.write_text("bad")

        version_result = MagicMock(stdout="typst 0.13.0")
        compile_result = MagicMock(returncode=1, stderr="error: syntax")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", side_effect=[version_result, compile_result]),
        ):
            result = runner.invoke(app, ["compile", str(typ_file)])
        assert result.exit_code == 1
        assert "failed" in result.output

    def test_compile_md_no_template_non_interactive_errors(self, tmp_path: Path) -> None:
        """Non-interactive terminal without --template should error with hint."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Hello")

        # Install a template so the error is about interactivity, not missing templates
        tpl_dir = tmp_path / "installed" / "proposal"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "typst.toml").write_text(
            '[package]\nname = "proposal"\nversion = "0.1.0"\ndescription = "A proposal."\n'
        )

        version_result = MagicMock(stdout="typst 0.13.0")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", return_value=version_result),
            patch("tai.commands.pdf.templates_install_dir", return_value=tmp_path / "installed"),
            patch("tai.commands.pdf.is_interactive", return_value=False),
        ):
            result = runner.invoke(app, ["compile", str(md_file)])
        assert result.exit_code == 1
        assert "not interactive" in result.output
        assert "proposal" in result.output

    def test_compile_md_no_template_no_installed_errors(self, tmp_path: Path) -> None:
        """No --template and no installed templates should error with setup hint."""
        md_file = tmp_path / "doc.md"
        md_file.write_text("# Hello")

        version_result = MagicMock(stdout="typst 0.13.0")

        with (
            patch("shutil.which", return_value="/usr/bin/typst"),
            patch("subprocess.run", return_value=version_result),
            patch("tai.commands.pdf.templates_install_dir", return_value=tmp_path / "empty"),
        ):
            result = runner.invoke(app, ["compile", str(md_file)])
        assert result.exit_code == 1
        assert "No templates installed" in result.output
        assert "setup-templates" in result.output


# ── templates command tests ──────────────────────────────────────────────────


class TestTemplatesCmd:
    def test_list_installed(self, patch_dirs, install_dir: Path) -> None:
        """After setup, 'tai pdf templates' shows installed templates."""
        runner.invoke(app, ["setup-templates"])
        result = runner.invoke(app, ["templates"])
        assert result.exit_code == 0
        assert "proposal" in result.output

    def test_list_empty(self, tmp_path: Path) -> None:
        """No installed templates shows hint."""
        with patch("tai.commands.pdf.templates_install_dir", return_value=tmp_path / "empty"):
            result = runner.invoke(app, ["templates"])
        assert result.exit_code == 0
        assert "No templates installed" in result.output
        assert "setup-templates" in result.output

    def test_list_json(self, patch_dirs, install_dir: Path) -> None:
        runner.invoke(app, ["setup-templates"])
        result = runner.invoke(app, ["templates", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        names = [t["name"] for t in data["templates"]]
        assert "proposal" in names

    def test_list_json_empty(self, tmp_path: Path) -> None:
        with patch("tai.commands.pdf.templates_install_dir", return_value=tmp_path / "empty"):
            result = runner.invoke(app, ["templates", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["templates"] == []
