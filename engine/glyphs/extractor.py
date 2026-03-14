from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


# Standard output size for normalised glyphs.
STANDARD_SIZE = 256


class Glyph:
    """Represents a single extracted handwritten glyph."""

    def __init__(
        self,
        label: str,
        image_path: Path,
        width: int,
        height: int,
    ) -> None:
        """Initialise a glyph.

        Args:
            label: The character or identifier this glyph represents.
            image_path: Path to the cropped glyph image on disk.
            width: Pixel width of the glyph image.
            height: Pixel height of the glyph image.
        """
        self.label = label
        self.image_path = image_path
        self.width = width
        self.height = height


class GlyphExtractor:
    """Extracts, normalises, and persists individual glyphs from detected regions.

    Receives bounding-box crops from WorksheetDetector, applies thresholding
    and morphological clean-up, then saves each glyph as a transparent PNG
    ready for font-building.
    """

    def extract(
        self,
        image_path: Path,
        boxes: list[tuple[int, int, int, int]],
        output_dir: Path,
        labels: list[str] | None = None,
    ) -> list[Glyph]:
        """Extract glyphs from the specified bounding boxes in *image_path*.

        Args:
            image_path: Path to the source scanned image.
            boxes: List of (x, y, width, height) crops to extract.
            output_dir: Directory where individual glyph PNGs will be saved.
            labels: Optional list of character labels aligned with *boxes*.
                    Defaults to sequential indices when omitted.

        Returns:
            Ordered list of Glyph objects, one per bounding box.

        Raises:
            FileNotFoundError: If *image_path* does not exist.
            ValueError: If *labels* is provided but its length differs from *boxes*.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if labels is not None and len(labels) != len(boxes):
            raise ValueError(
                f"labels length ({len(labels)}) does not match "
                f"boxes length ({len(boxes)})"
            )

        image = cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Failed to read image: {image_path}")

        if labels is None:
            labels = [str(i) for i in range(len(boxes))]

        output_dir.mkdir(parents=True, exist_ok=True)

        glyphs: list[Glyph] = []
        for i, (box, label) in enumerate(zip(boxes, labels)):
            glyph = self._process_cell(image, box, label, output_dir, i)
            glyphs.append(glyph)

        return glyphs

    def _process_cell(
        self,
        image: np.ndarray,
        box: tuple[int, int, int, int],
        label: str,
        output_dir: Path,
        index: int,
    ) -> Glyph:
        """Process a single cell: crop, threshold, tight-crop, normalise, save.

        Args:
            image: The full source image as a BGR numpy array.
            box: Bounding box as (x, y, width, height).
            label: Character label for this glyph.
            output_dir: Directory to save the output PNG.
            index: Sequential index used in the output filename.

        Returns:
            A Glyph object pointing to the saved PNG.
        """
        x, y, w, h = box

        # Crop the cell region from the source image.
        cell = image[y : y + h, x : x + w]

        # Convert to grayscale.
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold to isolate ink (white ink on black bg in INV mode).
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11,
            C=5,
        )

        # Find tight bounding rect around ink pixels.
        coords = cv2.findNonZero(thresh)
        if coords is not None:
            bx, by, bw, bh = cv2.boundingRect(coords)

            # Add padding (10% of cell size).
            pad = max(int(0.1 * min(w, h)), 1)
            bx = max(bx - pad, 0)
            by = max(by - pad, 0)
            bw = min(bw + 2 * pad, thresh.shape[1] - bx)
            bh = min(bh + 2 * pad, thresh.shape[0] - by)

            tight = thresh[by : by + bh, bx : bx + bw]
        else:
            # No ink found — use the full thresholded cell.
            tight = thresh

        # Resize to standard size while preserving aspect ratio.
        th, tw = tight.shape[:2]
        scale = min(STANDARD_SIZE / tw, STANDARD_SIZE / th)
        new_w = int(tw * scale)
        new_h = int(th * scale)
        resized = cv2.resize(tight, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Place on a white-padded (zeros in INV) canvas centred.
        canvas = np.zeros((STANDARD_SIZE, STANDARD_SIZE), dtype=np.uint8)
        x_off = (STANDARD_SIZE - new_w) // 2
        y_off = (STANDARD_SIZE - new_h) // 2
        canvas[y_off : y_off + new_h, x_off : x_off + new_w] = resized

        # Build RGBA image: black ink on transparent background.
        # canvas holds the ink mask (255 = ink, 0 = background).
        rgba = np.zeros((STANDARD_SIZE, STANDARD_SIZE, 4), dtype=np.uint8)
        # RGB channels: 0 where ink, 255 where background (but background is
        # transparent so the RGB value there is irrelevant — keep it 0).
        # Alpha channel: opaque (255) where ink, transparent (0) elsewhere.
        rgba[:, :, 3] = canvas  # alpha = ink mask

        # Save as PNG.
        safe_label = label.replace("/", "_slash_").replace("\\", "_bslash_")
        filename = f"{index:04d}_{safe_label}.png"
        out_path = output_dir / filename
        cv2.imwrite(str(out_path), rgba)

        return Glyph(
            label=label,
            image_path=out_path,
            width=STANDARD_SIZE,
            height=STANDARD_SIZE,
        )
