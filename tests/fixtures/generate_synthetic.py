"""Generate a synthetic handwriting worksheet for E2E testing.

Uses the Caveat font (OFL-licensed) to render characters into the
same grid layout the WorksheetDetector expects. Produces a deterministic
PNG image that exercises the full extraction → font → render pipeline
with realistic character content.

Usage:
    python tests/fixtures/generate_synthetic.py [--output path.png]
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Layout constants — must match detector.py / generator.py
# ---------------------------------------------------------------------------
PAGE_W_MM = 11.0 * 25.4  # 279.4
PAGE_H_MM = 8.5 * 25.4  # 215.9
TARGET_DPI = 150
CELL_SIZE_MM = 28.0
LABEL_HEIGHT_MM = 4.0
MARKER_SIZE_MM = 8.0
MARGIN_X_MM = 15.0
MARGIN_Y_MM = 15.0
CELL_GAP_MM = 2.0
ROW_GAP_MM = 3.0
GRID_OFFSET_TOP_MM = 18.0
GRID_OFFSET_LEFT_MM = MARKER_SIZE_MM + 2.0

# Character set — same order as WorksheetGenerator
LOWERCASE = list("abcdefghijklmnopqrstuvwxyz")
UPPERCASE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = list("0123456789")
PUNCTUATION = list(".,!?:;'\"-_()/ &")

LOWERCASE_VARIANTS = 3
UPPERCASE_VARIANTS = 2
DIGIT_VARIANTS = 2
PUNCTUATION_VARIANTS = 1

COLS = 8

FIXTURE_DIR = Path(__file__).parent
FONT_PATH = FIXTURE_DIR / "Caveat-Variable.ttf"


def _mm_to_px(mm_val: float) -> int:
    return int(round(mm_val * TARGET_DPI / 25.4))


def _build_char_order() -> list[str]:
    """Build the character order matching the worksheet generator."""
    chars: list[str] = []
    for char in LOWERCASE:
        for _ in range(LOWERCASE_VARIANTS):
            chars.append(char)
    for char in UPPERCASE:
        for _ in range(UPPERCASE_VARIANTS):
            chars.append(char)
    for char in DIGITS:
        for _ in range(DIGIT_VARIANTS):
            chars.append(char)
    for char in PUNCTUATION:
        for _ in range(PUNCTUATION_VARIANTS):
            chars.append(char)
    chars.append(" ")
    return chars


def generate_synthetic_worksheet(output_path: Path | None = None, seed: int = 42) -> Path:
    """Generate a synthetic worksheet image with handwriting-style characters.

    Args:
        output_path: Where to save the PNG. Defaults to tests/fixtures/synthetic_worksheet.png.
        seed: Random seed for deterministic jitter.

    Returns:
        Path to the generated image.
    """
    if output_path is None:
        output_path = FIXTURE_DIR / "synthetic_worksheet.png"

    rng = random.Random(seed)

    # Image dimensions
    w = _mm_to_px(PAGE_W_MM)  # 1650
    h = _mm_to_px(PAGE_H_MM)  # 1275

    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    # Load handwriting font
    cell_px = _mm_to_px(CELL_SIZE_MM)
    font_size = int(cell_px * 0.65)  # Character fills ~65% of cell
    font = ImageFont.truetype(str(FONT_PATH), font_size)
    label_font = ImageFont.truetype(str(FONT_PATH), int(cell_px * 0.15))

    # Draw alignment markers (4 corners)
    marker_px = _mm_to_px(MARKER_SIZE_MM)
    margin_x_px = _mm_to_px(MARGIN_X_MM)
    margin_y_px = _mm_to_px(MARGIN_Y_MM)

    marker_positions = [
        (margin_x_px, margin_y_px),  # TL
        (w - margin_x_px - marker_px, margin_y_px),  # TR
        (margin_x_px, h - margin_y_px - marker_px),  # BL
        (w - margin_x_px - marker_px, h - margin_y_px - marker_px),  # BR
    ]
    for mx, my in marker_positions:
        draw.rectangle([mx, my, mx + marker_px, my + marker_px], fill="black")

    # Grid starting position
    grid_left = _mm_to_px(MARGIN_X_MM + GRID_OFFSET_LEFT_MM)
    grid_top = _mm_to_px(MARGIN_Y_MM + GRID_OFFSET_TOP_MM)
    col_stride = _mm_to_px(CELL_SIZE_MM + CELL_GAP_MM)
    row_stride = _mm_to_px(CELL_SIZE_MM + LABEL_HEIGHT_MM + ROW_GAP_MM)

    # Calculate max rows
    usable_h_mm = PAGE_H_MM - 2 * MARGIN_Y_MM - 20.0
    max_rows = int(usable_h_mm / (CELL_SIZE_MM + LABEL_HEIGHT_MM + CELL_GAP_MM))

    char_order = _build_char_order()
    cells_on_page = min(len(char_order), COLS * max_rows)

    for idx in range(cells_on_page):
        col = idx % COLS
        row = idx // COLS
        if row >= max_rows:
            break

        x = grid_left + col * col_stride
        y = grid_top + row * row_stride

        # Draw cell border (light gray like the real worksheet)
        draw.rectangle(
            [x, y, x + cell_px, y + cell_px],
            outline=(80, 80, 80),
            width=1,
        )

        # Draw guidelines (dashed lines inside cell)
        for frac in [0.25, 0.55, 0.80]:
            gy = y + int(cell_px * (1.0 - frac))
            draw.line(
                [(x + 3, gy), (x + cell_px - 3, gy)],
                fill=(220, 220, 220),
                width=1,
            )

        # Render character with slight random jitter
        char = char_order[idx]
        if char.strip():
            # Random offset for realism (seeded for determinism)
            jitter_x = rng.randint(-3, 3)
            jitter_y = rng.randint(-3, 3)
            rotation = rng.uniform(-4, 4)

            # Render character onto a small temp image for rotation
            char_img = Image.new("RGBA", (cell_px, cell_px), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)

            # Center the character in the cell
            bbox = font.getbbox(char)
            char_w = bbox[2] - bbox[0]
            char_h = bbox[3] - bbox[1]
            cx = (cell_px - char_w) // 2 + jitter_x
            cy = (cell_px - char_h) // 2 + jitter_y - bbox[1]

            # Draw in dark ink color (not pure black — simulates pen)
            ink_color = (
                rng.randint(10, 40),
                rng.randint(5, 25),
                rng.randint(15, 45),
            )
            char_draw.text((cx, cy), char, font=font, fill=ink_color)

            # Apply slight rotation
            char_img = char_img.rotate(rotation, resample=Image.BICUBIC, expand=False)

            # Paste onto worksheet
            img.paste(char_img, (x, y), char_img)

        # Label below cell
        label = char if char.strip() else "SPC"
        label_y = y + cell_px + 2
        draw.text(
            (x + cell_px // 2, label_y),
            label,
            font=label_font,
            fill=(130, 130, 130),
            anchor="mt",
        )

    img.save(output_path, "PNG")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic worksheet fixture")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: tests/fixtures/synthetic_worksheet.png)",
    )
    args = parser.parse_args()
    path = generate_synthetic_worksheet(args.output)
    print(f"Generated: {path} ({path.stat().st_size / 1024:.0f} KB)")
