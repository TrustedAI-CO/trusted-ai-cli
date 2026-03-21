"""Tests for tai.core.style — palette constants and style installer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tai.core.style import COLORS, PALETTE, StyleInstallError, install, _STYLE_FILE


class TestPaletteConstants:
    """Verify palette exports are well-formed."""

    def test_palette_has_six_colors(self):
        assert len(PALETTE) == 6

    def test_palette_entries_are_hex(self):
        for color in PALETTE:
            assert color.startswith("#")
            assert len(color) == 7

    def test_colors_dict_has_required_keys(self):
        required = {"navy", "blue", "sky", "accent", "amber", "teal", "warm", "dark", "gray"}
        assert required.issubset(COLORS.keys())

    def test_palette_matches_colors(self):
        expected = [COLORS["navy"], COLORS["blue"], COLORS["sky"],
                    COLORS["accent"], COLORS["amber"], COLORS["teal"]]
        assert PALETTE == expected


class TestBundledStyleFile:
    """Verify the .mplstyle asset ships correctly."""

    def test_style_file_exists(self):
        assert _STYLE_FILE.is_file(), f"Missing bundled style: {_STYLE_FILE}"

    def test_style_file_contains_prop_cycle(self):
        content = _STYLE_FILE.read_text()
        assert "axes.prop_cycle" in content

    def test_style_file_background_matches_document(self):
        content = _STYLE_FILE.read_text()
        assert "f4f1eb" in content


class TestInstall:
    """Test the install() function."""

    def test_install_copies_file(self, tmp_path):
        stylelib = tmp_path / "stylelib"
        mock_mpl = MagicMock()
        mock_mpl.get_configdir.return_value = str(tmp_path)

        with patch.dict("sys.modules", {"matplotlib": mock_mpl}):
            dest = install()

        assert dest.exists()
        assert dest.name == "trustedai.mplstyle"
        assert dest.parent == stylelib

    def test_install_creates_stylelib_dir(self, tmp_path):
        mock_mpl = MagicMock()
        mock_mpl.get_configdir.return_value = str(tmp_path)

        with patch.dict("sys.modules", {"matplotlib": mock_mpl}):
            install()

        assert (tmp_path / "stylelib").is_dir()

    def test_install_raises_when_matplotlib_missing(self):
        with patch.dict("sys.modules", {"matplotlib": None}):
            with pytest.raises(StyleInstallError, match="matplotlib is not installed"):
                install()

    def test_install_raises_on_permission_error(self, tmp_path):
        mock_mpl = MagicMock()
        mock_mpl.get_configdir.return_value = str(tmp_path)

        with patch.dict("sys.modules", {"matplotlib": mock_mpl}), \
             patch("tai.core.style.shutil.copy2", side_effect=PermissionError("denied")):
            with pytest.raises(StyleInstallError, match="permissions"):
                install()
