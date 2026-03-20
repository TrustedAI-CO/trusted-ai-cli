"""Tests for tai.core.templates — discovery, parsing, installation."""

from __future__ import annotations

from pathlib import Path

import pytest

from tai.core.templates import (
    validate_template_name,
    parse_typst_toml,
    discover_templates,
    install_templates,
    remove_templates,
    templates_install_dir,
    TemplateInfo,
    InstallResult,
)


# ── validate_template_name ─────────────────────────────────────────────


class TestValidateTemplateName:
    def test_valid_names(self):
        assert validate_template_name("article") is True
        assert validate_template_name("my-template") is True
        assert validate_template_name("template_v2") is True
        assert validate_template_name("Report01") is True

    def test_path_traversal(self):
        assert validate_template_name("../etc/passwd") is False
        assert validate_template_name("..") is False
        assert validate_template_name("foo/../bar") is False

    def test_invalid_chars(self):
        assert validate_template_name("") is False
        assert validate_template_name(".hidden") is False
        assert validate_template_name("-starts-dash") is False
        assert validate_template_name("has space") is False
        assert validate_template_name("has/slash") is False


# ── parse_typst_toml ───────────────────────────────────────────────────


class TestParseTypstToml:
    def test_full_manifest(self, tmp_path: Path):
        toml_file = tmp_path / "typst.toml"
        toml_file.write_text(
            '[package]\n'
            'name = "article"\n'
            'version = "1.0.0"\n'
            'description = "Article template"\n'
        )
        info = parse_typst_toml(toml_file)
        assert info.name == "article"
        assert info.version == "1.0.0"
        assert info.description == "Article template"
        assert info.path == tmp_path

    def test_minimal_manifest(self, tmp_path: Path):
        toml_file = tmp_path / "typst.toml"
        toml_file.write_text("[package]\n")
        info = parse_typst_toml(toml_file)
        assert info.name == tmp_path.name
        assert info.version == "0.0.0"
        assert info.description == ""

    def test_empty_toml(self, tmp_path: Path):
        toml_file = tmp_path / "typst.toml"
        toml_file.write_text("")
        info = parse_typst_toml(toml_file)
        assert info.name == tmp_path.name


# ── discover_templates ─────────────────────────────────────────────────


class TestDiscoverTemplates:
    def test_finds_templates(self, tmp_path: Path):
        for name in ("article", "report"):
            d = tmp_path / name
            d.mkdir()
            (d / "typst.toml").write_text(
                f'[package]\nname = "{name}"\nversion = "1.0.0"\n'
            )
        # Non-template directory (no typst.toml)
        (tmp_path / "brand").mkdir()

        templates = discover_templates(tmp_path)
        assert len(templates) == 2
        names = [t.name for t in templates]
        assert "article" in names
        assert "report" in names

    def test_empty_dir(self, tmp_path: Path):
        assert discover_templates(tmp_path) == []

    def test_nonexistent_dir(self):
        assert discover_templates(Path("/nonexistent")) == []

    def test_skips_malformed_toml(self, tmp_path: Path):
        d = tmp_path / "broken"
        d.mkdir()
        (d / "typst.toml").write_text("not valid toml [[[")
        assert discover_templates(tmp_path) == []


# ── install_templates ──────────────────────────────────────────────────


class TestInstallTemplates:
    def _make_source(self, tmp_path: Path) -> Path:
        source = tmp_path / "source"
        source.mkdir()
        # Shared files
        (source / "theme.typ").write_text("// theme")
        brand = source / "brand"
        brand.mkdir()
        (brand / "logo.png").write_bytes(b"PNG")
        # Template packages
        for name in ("article", "report"):
            d = source / name
            d.mkdir()
            (d / "typst.toml").write_text(
                f'[package]\nname = "{name}"\nversion = "1.0.0"\n'
            )
            (d / "lib.typ").write_text(f"// {name} lib")
        return source

    def test_fresh_install(self, tmp_path: Path, monkeypatch):
        source = self._make_source(tmp_path)
        install_dir = tmp_path / "install"
        monkeypatch.setattr(
            "tai.core.templates.templates_install_dir", lambda: install_dir
        )
        result = install_templates(source)
        assert set(result.installed) == {"article", "report"}
        assert result.skipped == []
        # Shared files copied
        assert (install_dir / "theme.typ").is_file()
        assert (install_dir / "brand" / "logo.png").is_file()
        # Template packages copied
        assert (install_dir / "article" / "lib.typ").is_file()

    def test_skip_existing(self, tmp_path: Path, monkeypatch):
        source = self._make_source(tmp_path)
        install_dir = tmp_path / "install"
        monkeypatch.setattr(
            "tai.core.templates.templates_install_dir", lambda: install_dir
        )
        install_templates(source)
        result = install_templates(source)
        assert result.installed == []
        assert set(result.skipped) == {"article", "report"}

    def test_force_overwrite(self, tmp_path: Path, monkeypatch):
        source = self._make_source(tmp_path)
        install_dir = tmp_path / "install"
        monkeypatch.setattr(
            "tai.core.templates.templates_install_dir", lambda: install_dir
        )
        install_templates(source)
        result = install_templates(source, force=True)
        assert set(result.installed) == {"article", "report"}


# ── remove_templates ───────────────────────────────────────────────────


class TestRemoveTemplates:
    def test_removes_installed(self, tmp_path: Path, monkeypatch):
        install_dir = tmp_path / "templates"
        install_dir.mkdir()
        for name in ("article", "report"):
            d = install_dir / name
            d.mkdir()
            (d / "typst.toml").write_text("[package]\n")
            (d / "lib.typ").write_text("// lib")
        monkeypatch.setattr(
            "tai.core.templates.templates_install_dir", lambda: install_dir
        )
        count = remove_templates()
        assert count == 2
        assert not (install_dir / "article").exists()

    def test_empty_dir(self, tmp_path: Path, monkeypatch):
        install_dir = tmp_path / "templates"
        install_dir.mkdir()
        monkeypatch.setattr(
            "tai.core.templates.templates_install_dir", lambda: install_dir
        )
        assert remove_templates() == 0

    def test_nonexistent_dir(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "tai.core.templates.templates_install_dir", lambda: tmp_path / "nope"
        )
        assert remove_templates() == 0
