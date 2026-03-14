"""Handwriting renderer — renders text as handwriting-style images.

Uses PIL/Pillow with a custom TTF font to produce PNG images that mimic
natural handwriting with slight per-glyph variation.
"""

from __future__ import annotations

import math
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
    variation, character spacing jitter, glyph rotation, line drift,
    and word spacing randomization.
    """

    # Baseline jitter range (fraction of font_size)
    BASELINE_JITTER = 0.03
    # Horizontal spacing jitter range (fraction of font_size)
    SPACING_JITTER = 0.05
    # Rotation variation range in degrees
    ROTATION_RANGE = 1.0
    # Line drift range in degrees (slope across each line)
    LINE_DRIFT_RANGE = 0.5
    # Word spacing variation factor (0.8 = 80%, 1.2 = 120%)
    WORD_SPACE_MIN = 0.8
    WORD_SPACE_MAX = 1.2

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
        rng = random.Random(hash(text))  # deterministic jitter from text

        base_word_space = options.font_size // 2

        for line_idx, line in enumerate(lines):
            y = options.margin + line_idx * line_height
            x = options.margin

            # Line drift: gradual slope across the line
            drift_angle = rng.uniform(-self.LINE_DRIFT_RANGE, self.LINE_DRIFT_RANGE)
            drift_slope = math.tan(math.radians(drift_angle))

            for char in line:
                if char == " ":
                    word_factor = rng.uniform(self.WORD_SPACE_MIN, self.WORD_SPACE_MAX)
                    x += int(base_word_space * word_factor)
                    continue

                # Apply jitter
                jitter_y = int(rng.uniform(-1, 1) * options.font_size * self.BASELINE_JITTER)
                jitter_x = int(rng.uniform(-1, 1) * options.font_size * self.SPACING_JITTER)

                # Line drift offset based on horizontal position
                drift_y = int((x - options.margin) * drift_slope)

                # Rotation variation
                rotation = rng.uniform(-self.ROTATION_RANGE, self.ROTATION_RANGE)

                char_x = x + jitter_x
                char_y = y + jitter_y + drift_y

                if abs(rotation) > 0.1:
                    # Render glyph to temporary image, rotate, then paste
                    glyph_size = options.font_size * 2
                    glyph_img = Image.new("RGBA", (glyph_size, glyph_size), (0, 0, 0, 0))
                    glyph_draw = ImageDraw.Draw(glyph_img)
                    glyph_draw.text(
                        (glyph_size // 4, glyph_size // 4),
                        char,
                        font=font,
                        fill=(*options.color, 255),
                    )
                    rotated = glyph_img.rotate(rotation, resample=Image.BICUBIC, expand=False)
                    # Paste onto main image with alpha mask
                    paste_x = char_x - glyph_size // 4
                    paste_y = char_y - glyph_size // 4
                    if 0 <= paste_x < options.width and 0 <= paste_y < total_height:
                        img.paste(
                            Image.new("RGB", rotated.size, options.color),
                            (paste_x, paste_y),
                            rotated.split()[3],  # alpha channel as mask
                        )
                else:
                    # No rotation — draw directly (faster)
                    draw = ImageDraw.Draw(img)
                    draw.text(
                        (char_x, char_y),
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

        # Crop to actual content height
        actual_y = options.margin + len(lines) * line_height + options.margin
        actual_height = min(actual_y, total_height)
        if actual_height < total_height:
            img = img.crop((0, 0, options.width, actual_height))

        img.save(str(output_path), "PNG")
        return output_path

    def render_pdf(
        self,
        text: str,
        options: RenderOptions,
        output_path: Path,
    ) -> tuple[Path, int, int]:
        """Render *text* as a handwritten-style PDF document.

        Renders to PNG internally, then wraps the result in a single-page
        PDF using reportlab. The PDF page is sized to fit the rendered image.

        Args:
            text: The text content to render.
            options: Rendering configuration.
            output_path: Destination path for the output PDF file.

        Returns:
            Tuple of (resolved output path, image width, image height).
        """
        from reportlab.pdfgen import canvas

        # Render to a temporary PNG first
        png_path = output_path.with_suffix(".tmp.png")
        self.render(text, options, png_path)

        # Read the PNG to get dimensions
        with Image.open(png_path) as img:
            img_width, img_height = img.size

        # Create PDF sized to the image (at 72 DPI)
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(output_path), pagesize=(img_width, img_height))
        c.drawImage(str(png_path), 0, 0, img_width, img_height)
        c.save()

        # Clean up temporary PNG
        png_path.unlink(missing_ok=True)

        return output_path, img_width, img_height
