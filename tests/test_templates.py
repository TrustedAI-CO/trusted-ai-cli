"""Tests for tai.core.templates — template discovery, parsing, and installation."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from tai.core.templates import (
    InstallResult,
    TemplateInfo,
    discover_templates,
    install_brand,
    install_templates,
    parse_typst_toml,
    remove_templates,
    validate_template_name,
)


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def template_source(tmp_path: Path) -> Path:
    """Create a source directory with two valid templates."""
    for name in ("proposal", "report"):
        tpl_dir = tmp_path / name
        tpl_dir.mkdir()
        (tpl_dir / "typst.toml").write_text(
            f'[package]\nname = "{name}"\nversion = "0.1.0"\n'
            f'description = "A {name} template."\nentrypoint = "lib.typ"\n'
        )
        (tpl_dir / "lib.typ").write_text(f"// {name} template\n")
        tpl_sub = tpl_dir / "template"
        tpl_sub.mkdir()
        (tpl_sub / "main.typ").write_text(f"// {name} main\n")
    return tmp_path


@pytest.fixture
def install_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect template install directory to tmp_path."""
    target = tmp_path / "install"
    monkeypatch.setattr(
        "tai.core.templates.templates_install_dir", lambda: target
    )
    return target


@pytest.fixture
def brand_source(tmp_path: Path) -> Path:
    """Create a source directory with brand assets."""
    brand = tmp_path / "brand"
    brand.mkdir()
    (brand / "brand.toml").write_text(
        '[company]\nname = "TestCo"\n[colors]\nprimary = "#000000"\n'
    )
    return brand


@pytest.fixture
def brand_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect brand install directory to tmp_path."""
    target = tmp_path / "brand_install"
    monkeypatch.setattr(
        "tai.core.templates.brand_install_dir", lambda: target
    )
    return target


# ── validate_template_name ───────────────────────────────────────────────────


class TestValidateTemplateName:
    def test_valid_names(self) -> None:
        assert validate_template_name("proposal") is True
        assert validate_template_name("tech-report") is True
        assert validate_template_name("my_template_v2") is True
        assert validate_template_name("Report123") is True

    def test_path_traversal(self) -> None:
        assert validate_template_name("../../etc/passwd") is False
        assert validate_template_name("../secrets") is False

    def test_empty_string(self) -> None:
        assert validate_template_name("") is False

    def test_starts_with_special(self) -> None:
        assert validate_template_name("-leading-dash") is False
        assert validate_template_name("_leading-underscore") is False

    def test_special_chars(self) -> None:
        assert validate_template_name("hello world") is False
        assert validate_template_name("hello/world") is False


# ── parse_typst_toml ─────────────────────────────────────────────────────────


class TestParseTypstToml:
    def test_happy_path(self, template_source: Path) -> None:
        info = parse_typst_toml(template_source / "proposal" / "typst.toml")
        assert info.name == "proposal"
        assert info.version == "0.1.0"
        assert info.description == "A proposal template."

    def test_missing_fields_defaults(self, tmp_path: Path) -> None:
        manifest = tmp_path / "typst.toml"
        manifest.write_text("[package]\n")
        info = parse_typst_toml(manifest)
        assert info.name == tmp_path.name
        assert info.version == "0.0.0"
        assert info.description == ""

    def test_invalid_toml_raises(self, tmp_path: Path) -> None:
        manifest = tmp_path / "typst.toml"
        manifest.write_text("{broken toml")
        with pytest.raises(tomllib.TOMLDecodeError):
            parse_typst_toml(manifest)

    def test_no_package_section(self, tmp_path: Path) -> None:
        manifest = tmp_path / "typst.toml"
        manifest.write_text('title = "hello"\n')
        info = parse_typst_toml(manifest)
        assert info.name == tmp_path.name
        assert info.version == "0.0.0"


# ── discover_templates ───────────────────────────────────────────────────────


class TestDiscoverTemplates:
    def test_finds_templates(self, template_source: Path) -> None:
        templates = discover_templates(template_source)
        names = [t.name for t in templates]
        assert "proposal" in names
        assert "report" in names

    def test_skips_dirs_without_manifest(self, tmp_path: Path) -> None:
        (tmp_path / "no-manifest").mkdir()
        templates = discover_templates(tmp_path)
        assert templates == []

    def test_skips_invalid_toml(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad"
        bad.mkdir()
        (bad / "typst.toml").write_text("{broken")
        templates = discover_templates(tmp_path)
        assert templates == []

    def test_empty_dir(self, tmp_path: Path) -> None:
        templates = discover_templates(tmp_path)
        assert templates == []

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        templates = discover_templates(tmp_path / "nope")
        assert templates == []


# ── install_templates ────────────────────────────────────────────────────────


class TestInstallTemplates:
    def test_happy_path(
        self, template_source: Path, install_dir: Path
    ) -> None:
        result = install_templates(template_source)
        assert set(result.installed) == {"proposal", "report"}
        assert result.skipped == []
        assert (install_dir / "proposal" / "typst.toml").is_file()
        assert (install_dir / "report" / "lib.typ").is_file()

    def test_skip_existing(
        self, template_source: Path, install_dir: Path
    ) -> None:
        install_templates(template_source)
        result = install_templates(template_source)
        assert result.installed == []
        assert set(result.skipped) == {"proposal", "report"}

    def test_force_overwrite(
        self, template_source: Path, install_dir: Path
    ) -> None:
        install_templates(template_source)
        result = install_templates(template_source, force=True)
        assert set(result.installed) == {"proposal", "report"}
        assert result.skipped == []


# ── remove_templates ─────────────────────────────────────────────────────────


class TestRemoveTemplates:
    def test_remove_installed(
        self, template_source: Path, install_dir: Path
    ) -> None:
        install_templates(template_source)
        count = remove_templates()
        assert count == 2
        assert not (install_dir / "proposal").exists()

    def test_remove_empty(self, install_dir: Path) -> None:
        count = remove_templates()
        assert count == 0

    def test_remove_nonexistent_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "tai.core.templates.templates_install_dir",
            lambda: tmp_path / "nonexistent",
        )
        count = remove_templates()
        assert count == 0


# ── install_brand ────────────────────────────────────────────────────────────


class TestInstallBrand:
    def test_happy_path(
        self,
        brand_source: Path,
        brand_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "tai.core.templates.brand_install_dir", lambda: brand_dir
        )
        install_brand(brand_source)
        assert (brand_dir / "brand.toml").is_file()

    def test_overwrites_existing(
        self,
        brand_source: Path,
        brand_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "tai.core.templates.brand_install_dir", lambda: brand_dir
        )
        brand_dir.mkdir(parents=True)
        (brand_dir / "old_file.txt").write_text("old")
        install_brand(brand_source)
        assert not (brand_dir / "old_file.txt").exists()
        assert (brand_dir / "brand.toml").is_file()
