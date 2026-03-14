from __future__ import annotations

from pathlib import Path


class DetectionResult:
    """Holds the bounding boxes and metadata returned by the detector."""

    def __init__(self, boxes: list[tuple[int, int, int, int]], source: Path) -> None:
        """Initialise a detection result.

        Args:
            boxes: List of (x, y, width, height) bounding boxes for each glyph region.
            source: Path to the image that was analysed.
        """
        self.boxes = boxes
        self.source = source


class WorksheetDetector:
    """Detects and segments individual glyph cells from a scanned worksheet image.

    Uses classical computer-vision techniques (via OpenCV / scikit-image) to
    locate the printed grid, correct for perspective distortion, and isolate
    each handwritten cell.
    """

    def detect(self, image_path: Path) -> DetectionResult:
        """Segment glyph regions from a scanned worksheet image.

        Args:
            image_path: Path to the scanned worksheet image (JPEG, PNG, or TIFF).

        Returns:
            A DetectionResult containing bounding boxes for every detected glyph cell.

        Raises:
            FileNotFoundError: If *image_path* does not exist.
            ValueError: If the image cannot be parsed or no grid is detected.
        """
        pass
