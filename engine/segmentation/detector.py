"""Worksheet detector for segmenting scanned handwriting worksheets.

Locates alignment markers, corrects perspective, decodes QR metadata,
and returns bounding boxes for each character cell.
"""

from __future__ import annotations

import json
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Layout constants (must match generator.py)
# ---------------------------------------------------------------------------
CELL_SIZE_MM = 28.0
LABEL_HEIGHT_MM = 4.0
MARKER_SIZE_MM = 8.0
MARGIN_X_MM = 15.0
MARGIN_Y_MM = 15.0
QR_SIZE_MM = 25.0
CELL_GAP_MM = 2.0  # horizontal gap between cells
ROW_GAP_MM = 3.0  # extra vertical gap per row (label + spacing)
GRID_OFFSET_TOP_MM = 18.0  # grid starts this far below the top margin
GRID_OFFSET_LEFT_MM = MARKER_SIZE_MM + 2.0  # grid starts right of marker

# Landscape US Letter in mm (11 × 8.5 inches)
PAGE_W_MM = 11.0 * 25.4  # 279.4
PAGE_H_MM = 8.5 * 25.4  # 215.9

# Target DPI for the corrected image
TARGET_DPI = 150

DEFAULT_COLS = 8


def _mm_to_px(mm_val: float, dpi: int = TARGET_DPI) -> float:
    """Convert millimetres to pixels at the given DPI."""
    return mm_val * dpi / 25.4


# Target corrected image dimensions in pixels
TARGET_W = int(round(_mm_to_px(PAGE_W_MM)))
TARGET_H = int(round(_mm_to_px(PAGE_H_MM)))


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------
@dataclass
class DetectionResult:
    """Holds the bounding boxes and metadata returned by the detector."""

    boxes: list[tuple[int, int, int, int]]
    source: Path
    corrected_image_path: Path | None = None
    qr_metadata: dict[str, object] | None = None
    cell_labels: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------
class WorksheetDetector:
    """Detects and segments individual glyph cells from a scanned worksheet image.

    Uses classical computer-vision techniques (via OpenCV) to locate the
    printed grid, correct for perspective distortion, and isolate each
    handwritten cell.
    """

    # Marker detection tuning
    _MARKER_AREA_MIN_RATIO = 0.001  # min contour area relative to image
    _MARKER_AREA_MAX_RATIO = 0.02  # max contour area relative to image
    _SQUARE_ASPECT_TOL = 0.35  # max |1 - aspect_ratio| for a square
    _APPROX_POLY_TOLERANCE = 0.04  # epsilon fraction for contour approx

    def detect(self, image_path: Path) -> DetectionResult:
        """Segment glyph regions from a scanned worksheet image.

        Args:
            image_path: Path to the scanned worksheet image (JPEG, PNG, or TIFF).

        Returns:
            A DetectionResult containing bounding boxes for every detected
            glyph cell.

        Raises:
            FileNotFoundError: If *image_path* does not exist.
            ValueError: If the image cannot be parsed or no grid is detected.
        """
        image_path = Path(image_path).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Step 1 — find the four alignment markers
        try:
            marker_centers = self._find_markers(img)
            # Step 2 — perspective correction
            corrected = self._correct_perspective(img, marker_centers)
        except ValueError:
            logger.warning("Markers not found; falling back to simple resize")
            corrected = cv2.resize(img, (TARGET_W, TARGET_H), interpolation=cv2.INTER_AREA)

        # Save corrected image
        corrected_path = self._save_corrected(corrected, image_path)

        # Step 3 — decode QR metadata (best-effort)
        qr_metadata = self._decode_qr(corrected)

        # Step 4 — compute cell grid bounding boxes
        cols = DEFAULT_COLS
        cell_count: int | None = None
        cell_labels: list[str] = []

        if qr_metadata is not None:
            cols = int(qr_metadata.get("cols", DEFAULT_COLS))
            cell_count = qr_metadata.get("cell_count")  # type: ignore[assignment]
            if cell_count is not None:
                cell_count = int(cell_count)
            cells_list = qr_metadata.get("cells")
            if isinstance(cells_list, list):
                cell_labels = [
                    c.get("l", f"cell_{i}") if isinstance(c, dict) else f"cell_{i}"
                    for i, c in enumerate(cells_list)
                ]

        boxes = self._compute_cell_boxes(cols, cell_count)

        # Fill in default labels if QR didn't provide them
        if len(cell_labels) < len(boxes):
            for i in range(len(cell_labels), len(boxes)):
                cell_labels.append(f"cell_{i}")

        return DetectionResult(
            boxes=boxes,
            source=image_path,
            corrected_image_path=corrected_path,
            qr_metadata=qr_metadata,
            cell_labels=cell_labels[:len(boxes)],
        )

    # ------------------------------------------------------------------
    # Marker detection
    # ------------------------------------------------------------------
    def _find_markers(self, img: NDArray[np.uint8]) -> NDArray[np.float32]:
        """Find the four corner alignment markers.

        Returns an array of shape (4, 2) with centres ordered:
        top-left, top-right, bottom-left, bottom-right.

        Raises:
            ValueError: If fewer than 4 candidate markers are found.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Adaptive threshold to handle uneven lighting from scanners
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 15
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = img.shape[:2]
        total_area = h * w
        min_area = total_area * self._MARKER_AREA_MIN_RATIO
        max_area = total_area * self._MARKER_AREA_MAX_RATIO

        candidates: list[tuple[float, float]] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue

            # Approximate to polygon — markers should be roughly quadrilateral
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, self._APPROX_POLY_TOLERANCE * peri, True)
            if len(approx) < 4 or len(approx) > 8:
                continue

            # Check squareness via bounding rect aspect ratio
            bx, by, bw, bh = cv2.boundingRect(cnt)
            if bh == 0 or bw == 0:
                continue
            aspect = bw / bh
            if abs(1.0 - aspect) > self._SQUARE_ASPECT_TOL:
                continue

            # Solidity check — filled squares should be close to 1.0
            hull_area = cv2.contourArea(cv2.convexHull(cnt))
            if hull_area == 0:
                continue
            solidity = area / hull_area
            if solidity < 0.8:
                continue

            cx = bx + bw / 2.0
            cy = by + bh / 2.0
            candidates.append((cx, cy))

        if len(candidates) < 4:
            raise ValueError(
                f"Found only {len(candidates)} marker candidates; need 4. "
                "Check image quality and alignment marker visibility."
            )

        # Assign candidates to corners by proximity
        return self._assign_corners(candidates, w, h)

    @staticmethod
    def _assign_corners(
        candidates: list[tuple[float, float]], img_w: int, img_h: int
    ) -> NDArray[np.float32]:
        """Assign candidate centres to TL, TR, BL, BR corners.

        When there are more than 4 candidates, pick the one closest to each
        ideal corner position.
        """
        corners = np.array(
            [
                [0.0, 0.0],  # TL
                [img_w, 0.0],  # TR
                [0.0, img_h],  # BL
                [img_w, img_h],  # BR
            ],
            dtype=np.float32,
        )

        pts = np.array(candidates, dtype=np.float32)
        result = np.zeros((4, 2), dtype=np.float32)
        used: set[int] = set()

        for ci in range(4):
            dists = np.linalg.norm(pts - corners[ci], axis=1)
            # Mask already-used indices with inf
            for u in used:
                dists[u] = np.inf
            best = int(np.argmin(dists))
            result[ci] = pts[best]
            used.add(best)

        return result

    # ------------------------------------------------------------------
    # Perspective correction
    # ------------------------------------------------------------------
    def _correct_perspective(
        self, img: NDArray[np.uint8], marker_centers: NDArray[np.float32]
    ) -> NDArray[np.uint8]:
        """Warp the image so the worksheet is flat and axis-aligned.

        Args:
            img: Original BGR image.
            marker_centers: 4×2 array ordered TL, TR, BL, BR.

        Returns:
            Perspective-corrected image at TARGET_W × TARGET_H.
        """
        # Source points are the detected marker centres
        src = marker_centers.astype(np.float32)

        # Destination points: where the marker centres *should* land in the
        # corrected image.  Markers sit at (MARGIN + MARKER/2) from each edge.
        mx = _mm_to_px(MARGIN_X_MM + MARKER_SIZE_MM / 2.0)
        my = _mm_to_px(MARGIN_Y_MM + MARKER_SIZE_MM / 2.0)

        dst = np.array(
            [
                [mx, my],  # TL
                [TARGET_W - mx, my],  # TR
                [mx, TARGET_H - my],  # BL
                [TARGET_W - mx, TARGET_H - my],  # BR
            ],
            dtype=np.float32,
        )

        matrix = cv2.getPerspectiveTransform(src, dst)
        corrected: NDArray[np.uint8] = cv2.warpPerspective(
            img, matrix, (TARGET_W, TARGET_H), flags=cv2.INTER_LINEAR
        )
        return corrected

    # ------------------------------------------------------------------
    # QR decoding
    # ------------------------------------------------------------------
    @staticmethod
    def _decode_qr(corrected: NDArray[np.uint8]) -> dict[str, object] | None:
        """Attempt to decode the QR code from the top-right area.

        Returns parsed JSON dict or None on failure.
        """
        # Crop the QR region generously (top-right quadrant)
        h, w = corrected.shape[:2]
        qr_roi = corrected[0 : h // 3, w // 2 :]

        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(qr_roi)

        if not data:
            # Try on the full image as fallback
            data, _, _ = detector.detectAndDecode(corrected)

        if not data:
            logger.warning("QR code could not be decoded; using layout defaults")
            return None

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError:
            logger.warning("QR code data is not valid JSON: %s", data[:120])
            return None

        if not isinstance(parsed, dict):
            logger.warning("QR code JSON is not a dict")
            return None

        return parsed  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Cell grid computation
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_cell_boxes(
        cols: int,
        cell_count: int | None = None,
    ) -> list[tuple[int, int, int, int]]:
        """Compute (x, y, w, h) bounding boxes in the corrected-image pixel space.

        The layout replicates the generator's grid positioning, converted
        from mm to pixels at TARGET_DPI.
        """
        grid_left_px = _mm_to_px(MARGIN_X_MM + GRID_OFFSET_LEFT_MM)
        grid_top_px = _mm_to_px(MARGIN_Y_MM + GRID_OFFSET_TOP_MM)
        cell_px = _mm_to_px(CELL_SIZE_MM)
        col_stride_px = _mm_to_px(CELL_SIZE_MM + CELL_GAP_MM)
        row_stride_px = _mm_to_px(CELL_SIZE_MM + LABEL_HEIGHT_MM + ROW_GAP_MM)

        # Estimate max rows that fit if cell_count is unknown
        usable_h_mm = PAGE_H_MM - 2 * MARGIN_Y_MM - 20.0  # same calc as generator
        max_rows = int(usable_h_mm / (CELL_SIZE_MM + LABEL_HEIGHT_MM + CELL_GAP_MM))

        if cell_count is None:
            cell_count = cols * max_rows

        boxes: list[tuple[int, int, int, int]] = []
        for idx in range(cell_count):
            col = idx % cols
            row = idx // cols
            if row >= max_rows:
                break

            x = int(round(grid_left_px + col * col_stride_px))
            y = int(round(grid_top_px + row * row_stride_px))
            w = int(round(cell_px))
            h = int(round(cell_px))
            boxes.append((x, y, w, h))

        return boxes

    # ------------------------------------------------------------------
    # File I/O helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _save_corrected(corrected: NDArray[np.uint8], source: Path) -> Path:
        """Save the perspective-corrected image to a temp directory.

        Returns the path to the saved file.
        """
        tmp_dir = Path(tempfile.mkdtemp(prefix="handwright_"))
        out_name = f"{source.stem}_corrected.png"
        out_path = tmp_dir / out_name
        cv2.imwrite(str(out_path), corrected)
        logger.info("Saved corrected image to %s", out_path)
        return out_path
