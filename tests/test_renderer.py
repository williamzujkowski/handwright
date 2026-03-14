"""Tests for the handwriting renderer."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from engine.renderer.handwriting import HandwritingRenderer, RenderOptions


@pytest.fixture
def font_path() -> Path:
    """Find a usable TTF font on the system."""
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    ]
    for p in candidates:
        if p.exists():
            return p
    pytest.skip("No system TTF font found for testing")


class TestHandwritingRenderer:
    """Tests for HandwritingRenderer."""

    def test_render_creates_png(self, font_path: Path, tmp_path: Path) -> None:
        renderer = HandwritingRenderer()
        options = RenderOptions(font_path=font_path, font_size=32)
        output = tmp_path / "test.png"

        result = renderer.render("Hello World", options, output)

        assert result.exists()
        assert result.suffix == ".png"

    def test_render_output_is_valid_image(self, font_path: Path, tmp_path: Path) -> None:
        renderer = HandwritingRenderer()
        options = RenderOptions(font_path=font_path)
        output = tmp_path / "test.png"

        renderer.render("Test text", options, output)

        img = Image.open(output)
        assert img.mode == "RGB"
        assert img.width > 0
        assert img.height > 0

    def test_render_multiline(self, font_path: Path, tmp_path: Path) -> None:
        renderer = HandwritingRenderer()
        options = RenderOptions(font_path=font_path)
        output = tmp_path / "multi.png"

        renderer.render("Line 1\nLine 2\nLine 3", options, output)

        img = Image.open(output)
        # Multi-line should be taller than single-line
        assert img.height > options.font_size * 2

    def test_render_empty_text_raises(self, font_path: Path, tmp_path: Path) -> None:
        renderer = HandwritingRenderer()
        options = RenderOptions(font_path=font_path)

        with pytest.raises(ValueError, match="empty"):
            renderer.render("", options, tmp_path / "err.png")

    def test_render_missing_font_raises(self, tmp_path: Path) -> None:
        renderer = HandwritingRenderer()
        options = RenderOptions(font_path=tmp_path / "nonexistent.ttf")

        with pytest.raises(FileNotFoundError):
            renderer.render("Hello", options, tmp_path / "err.png")

    def test_render_deterministic_jitter(self, font_path: Path, tmp_path: Path) -> None:
        """Same text should produce identical output (deterministic RNG)."""
        renderer = HandwritingRenderer()
        options = RenderOptions(font_path=font_path, font_size=32)

        out1 = tmp_path / "r1.png"
        out2 = tmp_path / "r2.png"
        renderer.render("Deterministic test", options, out1)
        renderer.render("Deterministic test", options, out2)

        assert out1.read_bytes() == out2.read_bytes()

    def test_render_custom_colors(self, font_path: Path, tmp_path: Path) -> None:
        renderer = HandwritingRenderer()
        options = RenderOptions(
            font_path=font_path,
            color=(0, 0, 255),
            background_color=(255, 255, 200),
        )
        output = tmp_path / "colored.png"

        renderer.render("Blue on cream", options, output)

        img = Image.open(output)
        # Check background pixel color
        bg_pixel = img.getpixel((0, 0))
        assert bg_pixel == (255, 255, 200)
