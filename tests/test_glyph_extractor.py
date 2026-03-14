"""Tests for the glyph extractor."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from engine.glyphs.extractor import Glyph, GlyphExtractor


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a test image with dark marks in known cell positions."""
    # Create a white image (simulating a scanned worksheet)
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255

    # Draw dark marks in specific cell positions to simulate handwriting
    # Cell 1 at (50, 50) size 100x100 — draw an "X"
    cv2.line(img, (60, 60), (140, 140), (20, 20, 20), 3)
    cv2.line(img, (140, 60), (60, 140), (20, 20, 20), 3)

    # Cell 2 at (200, 50) size 100x100 — draw a circle
    cv2.circle(img, (250, 100), 30, (20, 20, 20), 3)

    # Cell 3 at (50, 200) size 100x100 — empty (no handwriting)

    path = tmp_path / "test_scan.png"
    cv2.imwrite(str(path), img)
    return path


class TestGlyphExtractor:
    """Tests for GlyphExtractor."""

    def test_extract_returns_glyph_list(self, sample_image: Path, tmp_path: Path) -> None:
        extractor = GlyphExtractor()
        boxes = [(50, 50, 100, 100), (200, 50, 100, 100)]
        labels = ["X_1", "O_1"]
        output_dir = tmp_path / "glyphs"

        glyphs = extractor.extract(sample_image, boxes, output_dir, labels)

        assert len(glyphs) == 2
        assert all(isinstance(g, Glyph) for g in glyphs)

    def test_extract_creates_output_files(self, sample_image: Path, tmp_path: Path) -> None:
        extractor = GlyphExtractor()
        boxes = [(50, 50, 100, 100)]
        output_dir = tmp_path / "glyphs"

        glyphs = extractor.extract(sample_image, boxes, output_dir)

        assert glyphs[0].image_path.exists()
        assert glyphs[0].image_path.suffix == ".png"

    def test_extract_with_sequential_labels(self, sample_image: Path, tmp_path: Path) -> None:
        extractor = GlyphExtractor()
        boxes = [(50, 50, 100, 100), (200, 50, 100, 100)]
        output_dir = tmp_path / "glyphs"

        glyphs = extractor.extract(sample_image, boxes, output_dir)

        assert glyphs[0].label == "0"
        assert glyphs[1].label == "1"

    def test_extract_label_count_mismatch_raises(self, sample_image: Path, tmp_path: Path) -> None:
        extractor = GlyphExtractor()
        boxes = [(50, 50, 100, 100)]
        labels = ["a", "b"]  # mismatched count

        with pytest.raises(ValueError, match="labels"):
            extractor.extract(sample_image, boxes, tmp_path / "out", labels)

    def test_extract_missing_image_raises(self, tmp_path: Path) -> None:
        extractor = GlyphExtractor()
        with pytest.raises(FileNotFoundError):
            extractor.extract(
                tmp_path / "nonexistent.png",
                [(0, 0, 10, 10)],
                tmp_path / "out",
            )

    def test_extracted_glyph_has_dimensions(self, sample_image: Path, tmp_path: Path) -> None:
        extractor = GlyphExtractor()
        boxes = [(50, 50, 100, 100)]
        output_dir = tmp_path / "glyphs"

        glyphs = extractor.extract(sample_image, boxes, output_dir)

        assert glyphs[0].width > 0
        assert glyphs[0].height > 0
