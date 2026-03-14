from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from fontTools.ttLib import TTFont

from engine.fontgen.builder import FontBuilder, FontMetadata


def _create_glyph_image(path: Path, letter: str = "A") -> None:
    """Create a simple 100x100 RGBA PNG with a drawn letter shape."""
    img = np.zeros((100, 100, 4), dtype=np.uint8)

    if letter == "A":
        # Draw a triangle-like "A" shape
        pts = np.array([[50, 10], [20, 90], [40, 90], [50, 50], [60, 90], [80, 90]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.fillPoly(img, [pts], (255, 255, 255, 255))
    elif letter == "B":
        # Draw a rectangle-like "B" shape
        cv2.rectangle(img, (20, 10), (70, 90), (255, 255, 255, 255), -1)
        cv2.rectangle(img, (40, 30), (60, 70), (0, 0, 0, 0), -1)
    elif letter == "H":
        # Draw an H shape
        cv2.rectangle(img, (15, 10), (35, 90), (255, 255, 255, 255), -1)
        cv2.rectangle(img, (65, 10), (85, 90), (255, 255, 255, 255), -1)
        cv2.rectangle(img, (35, 35), (65, 55), (255, 255, 255, 255), -1)
    else:
        # Generic filled circle
        cv2.circle(img, (50, 50), 30, (255, 255, 255, 255), -1)

    cv2.imwrite(str(path), img)


@pytest.fixture()
def glyph_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample glyph images."""
    d = tmp_path / "glyphs"
    d.mkdir()
    for letter in ("A", "B", "H"):
        img_path = d / f"{letter}.png"
        _create_glyph_image(img_path, letter)
    return d


@pytest.fixture()
def glyph_map(glyph_dir: Path) -> dict[str, list[Path]]:
    """Return a glyph_map with three characters."""
    return {
        "A": [glyph_dir / "A.png"],
        "B": [glyph_dir / "B.png"],
        "H": [glyph_dir / "H.png"],
    }


class TestFontBuilder:
    def test_build_creates_ttf_file(self, tmp_path: Path, glyph_map: dict[str, list[Path]]) -> None:
        """build_ttf produces a valid TTF file on disk."""
        output = tmp_path / "out.ttf"
        builder = FontBuilder()
        result = builder.build_ttf(glyph_map, output)

        assert result.exists()
        assert result.suffix == ".ttf"
        # Verify it's actually parseable as a font
        font = TTFont(str(result))
        font.close()

    def test_build_empty_glyph_map_raises(self, tmp_path: Path) -> None:
        """An empty glyph_map raises ValueError."""
        builder = FontBuilder()
        with pytest.raises(ValueError, match="must not be empty"):
            builder.build_ttf({}, tmp_path / "out.ttf")

    def test_build_missing_image_raises(self, tmp_path: Path) -> None:
        """A glyph_map entry pointing to a non-existent file raises FileNotFoundError."""
        builder = FontBuilder()
        bad_map: dict[str, list[Path]] = {"X": [tmp_path / "nonexistent.png"]}
        with pytest.raises(FileNotFoundError, match="nonexistent.png"):
            builder.build_ttf(bad_map, tmp_path / "out.ttf")

    def test_built_font_has_correct_glyph_count(
        self, tmp_path: Path, glyph_map: dict[str, list[Path]]
    ) -> None:
        """The built font contains .notdef + space + one glyph per entry."""
        output = tmp_path / "out.ttf"
        builder = FontBuilder()
        builder.build_ttf(glyph_map, output)

        font = TTFont(str(output))
        glyph_order = font.getGlyphOrder()
        # .notdef + space + A + B + H = 5
        assert len(glyph_order) == 5
        assert ".notdef" in glyph_order
        assert "space" in glyph_order
        assert "A" in glyph_order
        assert "B" in glyph_order
        assert "H" in glyph_order
        font.close()

    def test_build_woff2_creates_valid_file(
        self, tmp_path: Path, glyph_map: dict[str, list[Path]]
    ) -> None:
        """build_woff2 produces a valid WOFF2 file readable by fontTools."""
        ttf_output = tmp_path / "out.ttf"
        woff2_output = tmp_path / "out.woff2"
        builder = FontBuilder()
        builder.build_ttf(glyph_map, ttf_output)
        result = builder.build_woff2(ttf_output, woff2_output)

        assert result.exists()
        assert result.suffix == ".woff2"
        # WOFF2 files start with the magic bytes 0x774F4632 ("wOF2")
        assert result.read_bytes()[:4] == b"wOF2"

    def test_build_woff2_missing_ttf_raises(self, tmp_path: Path) -> None:
        """build_woff2 raises FileNotFoundError when the source TTF is missing."""
        builder = FontBuilder()
        with pytest.raises(FileNotFoundError, match="TTF file not found"):
            builder.build_woff2(tmp_path / "missing.ttf", tmp_path / "out.woff2")

    def test_built_font_metadata(self, tmp_path: Path, glyph_map: dict[str, list[Path]]) -> None:
        """Custom metadata is reflected in the font name table."""
        output = tmp_path / "out.ttf"
        meta = FontMetadata(
            family_name="Test Hand",
            style_name="Bold",
            version="2.0",
            designer="Alice",
        )
        builder = FontBuilder()
        builder.build_ttf(glyph_map, output, metadata=meta)

        font = TTFont(str(output))
        name_table = font["name"]

        # nameID 1 = family name, nameID 2 = style name
        family = name_table.getDebugName(1)
        style = name_table.getDebugName(2)
        assert "Test Hand" in family
        assert "Bold" in style
        font.close()

    def test_built_font_contains_variant_glyphs(self, tmp_path: Path, glyph_dir: Path) -> None:
        """Alternate variant glyphs are stored as <base>.alt1, <base>.alt2, etc."""
        # A: 2 variants, B: 3 variants, H: 1 variant
        multi_map: dict[str, list[Path]] = {
            "A": [glyph_dir / "A.png", glyph_dir / "B.png"],
            "B": [glyph_dir / "B.png", glyph_dir / "A.png", glyph_dir / "H.png"],
            "H": [glyph_dir / "H.png"],
        }
        output = tmp_path / "variants.ttf"
        builder = FontBuilder()
        builder.build_ttf(multi_map, output)

        font = TTFont(str(output))
        glyph_order = font.getGlyphOrder()

        # Base glyphs must be present
        assert "A" in glyph_order
        assert "B" in glyph_order
        assert "H" in glyph_order

        # A has 2 variants: A (base) + A.alt1
        assert "A.alt1" in glyph_order
        assert "A.alt2" not in glyph_order

        # B has 3 variants: B (base) + B.alt1 + B.alt2
        assert "B.alt1" in glyph_order
        assert "B.alt2" in glyph_order

        # H has only 1 variant — no alt glyphs
        assert "H.alt1" not in glyph_order

        # Total: .notdef + space + A + A.alt1 + B + B.alt1 + B.alt2 + H = 8
        assert len(glyph_order) == 8
        # Total glyph count exceeds the number of unique characters (3)
        assert len(glyph_order) > 3 + 2  # 2 reserved (.notdef, space)

        font.close()
