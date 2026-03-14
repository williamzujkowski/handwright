from __future__ import annotations

from pathlib import Path


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
        pass
