"""Handwriting renderer — renders text as handwriting-style images.

Uses PIL/Pillow with a custom TTF font to produce PNG images that mimic
natural handwriting with slight per-glyph variation.
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


class RenderOptions:
    """Configuration options for the handwriting renderer."""

    def __init__(
        self,
        font_path: Path,
        font_size: int = 48,
        line_spacing: float = 1.5,
        color: tuple[int, int, int] = (0, 0, 0),
        background_color: tuple[int, int, int] = (255, 255, 255),
        width: int = 800,
        margin: int = 40,
    ) -> None:
        self.font_path = font_path
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.color = color
        self.background_color = background_color
        self.width = width
        self.margin = margin


class HandwritingRenderer:
    """Renders text as a handwriting-style image using a custom glyph font.

    Combines a generated .ttf font with layout logic to produce a PNG
    image that mimics natural handwriting, including slight baseline
    variation and character spacing jitter.
    """

    # Baseline jitter range in pixels (relative to font_size)
    BASELINE_JITTER = 0.03
    # Horizontal spacing jitter range in pixels
    SPACING_JITTER = 0.05

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
        if not text.strip():
            raise ValueError("Text must not be empty")

        if not options.font_path.exists():
            raise FileNotFoundError(f"Font not found: {options.font_path}")

        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        font = ImageFont.truetype(str(options.font_path), options.font_size)
        line_height = int(options.font_size * options.line_spacing)

        lines = text.split("\n")

        # Calculate image height
        total_height = 2 * options.margin + len(lines) * line_height + options.font_size
        total_height = max(total_height, options.margin * 2 + line_height)

        img = Image.new("RGB", (options.width, total_height), options.background_color)
        draw = ImageDraw.Draw(img)

        y = options.margin
        rng = random.Random(hash(text))  # deterministic jitter from text

        for line in lines:
            x = options.margin
            for char in line:
                if char == " ":
                    x += options.font_size // 2
                    continue

                # Apply slight jitter for natural feel
                jitter_y = int(rng.uniform(-1, 1) * options.font_size * self.BASELINE_JITTER)
                jitter_x = int(rng.uniform(-1, 1) * options.font_size * self.SPACING_JITTER)

                draw.text(
                    (x + jitter_x, y + jitter_y),
                    char,
                    font=font,
                    fill=options.color,
                )

                # Advance cursor by character width
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0] if bbox else options.font_size // 2
                x += char_width + jitter_x

                if x > options.width - options.margin:
                    break  # simple line-wrap

            y += line_height

        # Crop to actual content height
        actual_height = min(y + options.margin, total_height)
        if actual_height < total_height:
            img = img.crop((0, 0, options.width, actual_height))

        img.save(str(output_path), "PNG")
        return output_path
