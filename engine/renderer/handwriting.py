from __future__ import annotations

from pathlib import Path


class RenderOptions:
    """Configuration options for the handwriting renderer."""

    def __init__(
        self,
        font_path: Path,
        font_size: int = 48,
        line_spacing: float = 1.5,
        color: tuple[int, int, int] = (0, 0, 0),
        background_color: tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        """Initialise render options.

        Args:
            font_path: Path to the .ttf font file to use for rendering.
            font_size: Font size in points.
            line_spacing: Multiplier applied to the font's natural line height.
            color: RGB ink colour as an (R, G, B) tuple.
            background_color: RGB background colour as an (R, G, B) tuple.
        """
        self.font_path = font_path
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.color = color
        self.background_color = background_color


class HandwritingRenderer:
    """Renders text as a handwriting-style image using a custom glyph font.

    Combines glyph images (or a generated .ttf font) with layout logic to
    produce a PNG image that mimics natural handwriting, including slight
    per-glyph rotation and baseline variation.
    """

    def render(
        self,
        text: str,
        options: RenderOptions,
        output_path: Path,
    ) -> Path:
        """Render *text* as a handwritten-style PNG image.

        Args:
            text: The text content to render. Multi-line strings are supported.
            options: Rendering configuration (font, size, colours, spacing).
            output_path: Destination path for the output PNG file.

        Returns:
            The resolved path of the written PNG file.

        Raises:
            FileNotFoundError: If the font specified in *options* does not exist.
            ValueError: If *text* is empty.
        """
        pass
