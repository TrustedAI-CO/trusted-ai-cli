"""Tests for tai.core.config.load_brand_colors."""

from __future__ import annotations

from pathlib import Path

from tai.core.config import BrandColors, load_brand_colors


class TestLoadBrandColors:
    def test_with_full_brand_toml(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "brand.toml"
        toml_file.write_text(
            '[company]\nname = "TestCo"\ntagline = "We test."\n'
            '[colors]\nprimary = "#ff0000"\nsecondary = "#00ff00"\n'
            'accent = "#0000ff"\n'
        )
        brand = load_brand_colors(toml_file)
        assert brand.company_name == "TestCo"
        assert brand.company_tagline == "We test."
        assert brand.primary == "#ff0000"
        assert brand.secondary == "#00ff00"
        assert brand.accent == "#0000ff"

    def test_missing_file(self, tmp_path: Path) -> None:
        brand = load_brand_colors(tmp_path / "nonexistent.toml")
        assert brand == BrandColors()
        assert brand.company_name == "TrustedAI"
        assert brand.primary is None

    def test_malformed_toml(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "brand.toml"
        toml_file.write_text("this is not valid toml [[[")
        brand = load_brand_colors(toml_file)
        assert brand == BrandColors()

    def test_partial_config(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "brand.toml"
        toml_file.write_text('[company]\nname = "PartialCo"\n')
        brand = load_brand_colors(toml_file)
        assert brand.company_name == "PartialCo"
        assert brand.company_tagline is None
        assert brand.primary is None

    def test_empty_name_falls_back(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "brand.toml"
        toml_file.write_text('[company]\nname = ""\n')
        brand = load_brand_colors(toml_file)
        assert brand.company_name == "TrustedAI"

    def test_frozen_dataclass(self, tmp_path: Path) -> None:
        brand = load_brand_colors(tmp_path / "nonexistent.toml")
        with __import__("pytest").raises(AttributeError):
            brand.company_name = "Mutated"  # type: ignore[misc]
