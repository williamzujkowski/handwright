"""Tests for the worksheet detector."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from engine.segmentation.detector import DetectionResult, WorksheetDetector
from engine.worksheet.generator import (
    CELL_SIZE,
    MARKER_SIZE,
    MARGIN_X,
    MARGIN_Y,
    WorksheetConfig,
    WorksheetGenerator,
)


@pytest.fixture
def worksheet_pdf(tmp_path: Path) -> Path:
    """Generate a real worksheet PDF for testing."""
    generator = WorksheetGenerator()
    return generator.generate_pdf(tmp_path / "worksheet.pdf")


@pytest.fixture
def simple_image_with_markers(tmp_path: Path) -> Path:
    """Create a simple test image with 4 corner markers."""
    # Simulate a landscape-oriented scanned page
    h, w = 850, 1100  # ~100 DPI for letter landscape
    img = np.ones((h, w, 3), dtype=np.uint8) * 255

    marker_px = 30  # ~8mm at 100 DPI
    margin_px = 55  # ~15mm at 100 DPI

    # Draw 4 black square markers at corners
    positions = [
        (margin_px, margin_px),  # top-left
        (w - margin_px - marker_px, margin_px),  # top-right
        (margin_px, h - margin_px - marker_px),  # bottom-left
        (w - margin_px - marker_px, h - margin_px - marker_px),  # bottom-right
    ]
    for x, y in positions:
        cv2.rectangle(img, (x, y), (x + marker_px, y + marker_px), (0, 0, 0), -1)

    path = tmp_path / "scan_with_markers.png"
    cv2.imwrite(str(path), img)
    return path


class TestDetectionResult:
    """Tests for DetectionResult data class."""

    def test_stores_boxes_and_source(self, tmp_path: Path) -> None:
        boxes = [(10, 20, 30, 40)]
        result = DetectionResult(boxes=boxes, source=tmp_path / "img.png")
        assert result.boxes == boxes
        assert result.source == tmp_path / "img.png"


class TestWorksheetDetector:
    """Tests for WorksheetDetector."""

    def test_detect_missing_image_raises(self, tmp_path: Path) -> None:
        detector = WorksheetDetector()
        with pytest.raises(FileNotFoundError):
            detector.detect(tmp_path / "nonexistent.png")

    def test_detect_returns_detection_result(
        self, simple_image_with_markers: Path
    ) -> None:
        detector = WorksheetDetector()
        result = detector.detect(simple_image_with_markers)
        assert isinstance(result, DetectionResult)

    def test_detect_finds_cells(
        self, simple_image_with_markers: Path
    ) -> None:
        detector = WorksheetDetector()
        result = detector.detect(simple_image_with_markers)
        # Should find at least some cells from the grid layout
        assert len(result.boxes) > 0

    def test_detect_boxes_are_valid_tuples(
        self, simple_image_with_markers: Path
    ) -> None:
        detector = WorksheetDetector()
        result = detector.detect(simple_image_with_markers)
        for box in result.boxes:
            assert len(box) == 4
            x, y, w, h = box
            assert w > 0
            assert h > 0
