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
def glyph_map(glyph_dir: Path) -> dict[str, Path]:
    """Return a glyph_map with three characters."""
    return {
        "A": glyph_dir / "A.png",
        "B": glyph_dir / "B.png",
        "H": glyph_dir / "H.png",
    }


class TestFontBuilder:
    def test_build_creates_ttf_file(self, tmp_path: Path, glyph_map: dict[str, Path]) -> None:
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
        bad_map = {"X": tmp_path / "nonexistent.png"}
        with pytest.raises(FileNotFoundError, match="nonexistent.png"):
            builder.build_ttf(bad_map, tmp_path / "out.ttf")

    def test_built_font_has_correct_glyph_count(
        self, tmp_path: Path, glyph_map: dict[str, Path]
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

    def test_built_font_metadata(self, tmp_path: Path, glyph_map: dict[str, Path]) -> None:
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
