"""Worksheet PDF generator for handwriting capture.

Generates printable worksheets with labeled character cells, alignment markers,
and QR metadata for automated glyph extraction.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import qrcode
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# Character set specification
LOWERCASE = list("abcdefghijklmnopqrstuvwxyz")
UPPERCASE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = list("0123456789")
PUNCTUATION = list(".,!?:;'\"-_()/ &")
SYMBOLS = list("@#$%^*+=[]{}|<>~`\\")  # Extended symbols for full-set worksheets

LOWERCASE_VARIANTS = 3
UPPERCASE_VARIANTS = 2
DIGIT_VARIANTS = 2
PUNCTUATION_VARIANTS = 1
SYMBOL_VARIANTS = 1

# Layout constants
CELL_SIZE = 28 * mm  # 28mm cells
LABEL_HEIGHT = 4 * mm
GUIDELINE_COLOR = (0.85, 0.85, 0.85)  # Light gray
MARKER_SIZE = 8 * mm
MARGIN_X = 15 * mm
MARGIN_Y = 15 * mm
QR_SIZE = 25 * mm


@dataclass
class CellSpec:
    """Specification for a single character cell on the worksheet."""

    char: str
    variant: int
    label: str
    group: str = ""  # Section group: "lowercase", "uppercase", "digits", "punctuation"


@dataclass
class PageSpec:
    """Specification for a single worksheet page."""

    page_number: int
    cells: list[CellSpec]
    cols: int = 8
    title: str = ""


@dataclass
class WorksheetConfig:
    """Configuration for worksheet generation."""

    version: str = "1.0"
    cell_size_mm: float = 28.0
    cols_per_row: int = 8
    include_symbols: bool = False

    def build_pages(self) -> list[PageSpec]:
        """Build the page specifications for the full character set."""
        all_cells: list[CellSpec] = []

        # Lowercase: 3 variants each
        for char in LOWERCASE:
            for v in range(1, LOWERCASE_VARIANTS + 1):
                all_cells.append(
                    CellSpec(char=char, variant=v, label=f"{char}_{v}", group="lowercase")
                )

        # Uppercase: 2 variants each
        for char in UPPERCASE:
            for v in range(1, UPPERCASE_VARIANTS + 1):
                all_cells.append(
                    CellSpec(char=char, variant=v, label=f"{char}_{v}", group="uppercase")
                )

        # Digits: 2 variants each
        for char in DIGITS:
            for v in range(1, DIGIT_VARIANTS + 1):
                all_cells.append(
                    CellSpec(char=char, variant=v, label=f"{char}_{v}", group="digits")
                )

        # Punctuation: 1 variant each
        for char in PUNCTUATION:
            all_cells.append(
                CellSpec(
                    char=char, variant=1, label=f"p_{PUNCTUATION.index(char)}", group="punctuation"
                )
            )

        # Extended symbols (optional)
        if self.include_symbols:
            for char in SYMBOLS:
                for v in range(1, SYMBOL_VARIANTS + 1):
                    all_cells.append(
                        CellSpec(
                            char=char, variant=v, label=f"s_{SYMBOLS.index(char)}", group="symbols"
                        )
                    )

        # Space sampling cell
        all_cells.append(CellSpec(char=" ", variant=1, label="space", group="punctuation"))

        # Split into pages
        cells_per_page = self.cols_per_row * self._rows_per_page()
        pages: list[PageSpec] = []
        for i in range(0, len(all_cells), cells_per_page):
            page_cells = all_cells[i : i + cells_per_page]
            pages.append(
                PageSpec(
                    page_number=len(pages) + 1,
                    cells=page_cells,
                    cols=self.cols_per_row,
                    title=f"Handwright Worksheet — Page {len(pages) + 1}",
                )
            )

        return pages

    def _rows_per_page(self) -> int:
        """Calculate rows that fit on a landscape letter page."""
        page_w, page_h = landscape(LETTER)
        usable_height = page_h - 2 * MARGIN_Y - 20 * mm  # title + QR area
        return int(usable_height / (CELL_SIZE + LABEL_HEIGHT + 2 * mm))

    def to_metadata(self) -> dict[str, object]:
        """Generate metadata dict for QR encoding."""
        return {
            "v": self.version,
            "cell_mm": self.cell_size_mm,
            "cols": self.cols_per_row,
            "charset": "en_v1",
            "lc_variants": LOWERCASE_VARIANTS,
            "uc_variants": UPPERCASE_VARIANTS,
            "digit_variants": DIGIT_VARIANTS,
            "punct_variants": PUNCTUATION_VARIANTS,
        }


class WorksheetGenerator:
    """Generates printable handwriting worksheets as PDF files.

    Each worksheet includes:
    - Labeled character cells with handwriting guidelines
    - Corner alignment markers for perspective correction
    - QR metadata block for automated processing
    """

    def __init__(self, config: WorksheetConfig | None = None) -> None:
        self.config = config or WorksheetConfig()

    def generate_pdf(self, output_path: Path) -> Path:
        """Generate the complete worksheet PDF.

        Args:
            output_path: Destination path for the generated PDF file.

        Returns:
            The resolved path of the written PDF file.
        """
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        pages = self.config.build_pages()
        page_w, page_h = landscape(LETTER)

        c = canvas.Canvas(str(output_path), pagesize=landscape(LETTER))

        for page in pages:
            self._draw_page(c, page, page_w, page_h)
            c.showPage()

        c.save()
        return output_path

    def _draw_page(self, c: canvas.Canvas, page: PageSpec, page_w: float, page_h: float) -> None:
        """Draw a single worksheet page."""
        # Corner alignment markers
        self._draw_alignment_markers(c, page_w, page_h)

        # Title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(MARGIN_X + MARKER_SIZE + 5 * mm, page_h - MARGIN_Y - 5 * mm, page.title)

        # QR code (top right)
        self._draw_qr_code(c, page, page_w, page_h)

        # Section header labels
        group_labels = {
            "lowercase": "Lowercase (a–z) — 3 variants each",
            "uppercase": "Uppercase (A–Z) — 2 variants each",
            "digits": "Digits (0–9) — 2 variants each",
            "punctuation": "Punctuation — 1 variant each",
            "symbols": "Extended Symbols — 1 variant each",
        }

        # Draw section header at top of page if this page starts a new group
        # or continues the previous page's group
        first_group = page.cells[0].group if page.cells else ""
        subtitle = group_labels.get(first_group, "")
        if subtitle:
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.4, 0.4, 0.6)
            c.drawString(MARGIN_X + MARKER_SIZE + 5 * mm, page_h - MARGIN_Y - 14 * mm, subtitle)
            c.setFillColorRGB(0, 0, 0)

        # Character grid
        grid_top = page_h - MARGIN_Y - 18 * mm
        grid_left = MARGIN_X + MARKER_SIZE + 2 * mm

        row = 0
        col = 0
        current_group = first_group
        for cell in page.cells:
            # If group changes mid-page, insert a section label
            if cell.group != current_group and cell.group:
                if col > 0:
                    col = 0
                    row += 1
                label = group_labels.get(cell.group, "")
                if label:
                    label_y = grid_top - row * (CELL_SIZE + LABEL_HEIGHT + 3 * mm) + 2 * mm
                    c.setFont("Helvetica-Bold", 7)
                    c.setFillColorRGB(0.4, 0.4, 0.6)
                    c.drawString(grid_left, label_y, label)
                    c.setFillColorRGB(0, 0, 0)
                    row += 1
                current_group = cell.group
            x = grid_left + col * (CELL_SIZE + 2 * mm)
            y = grid_top - row * (CELL_SIZE + LABEL_HEIGHT + 3 * mm)

            self._draw_cell(c, cell, x, y)

            col += 1
            if col >= page.cols:
                col = 0
                row += 1

    def _draw_cell(self, c: canvas.Canvas, cell: CellSpec, x: float, y: float) -> None:
        """Draw a single character cell with guidelines."""
        # Cell border
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(0.5)
        c.rect(x, y - CELL_SIZE, CELL_SIZE, CELL_SIZE)

        # Guidelines (baseline, x-height, ascender, descender)
        c.setStrokeColorRGB(*GUIDELINE_COLOR)
        c.setLineWidth(0.3)
        c.setDash(2, 2)

        baseline_y = y - CELL_SIZE + CELL_SIZE * 0.25
        x_height_y = y - CELL_SIZE + CELL_SIZE * 0.55
        ascender_y = y - CELL_SIZE + CELL_SIZE * 0.80

        for gy in [baseline_y, x_height_y, ascender_y]:
            c.line(x + 1 * mm, gy, x + CELL_SIZE - 1 * mm, gy)

        c.setDash()  # Reset dash

        # Label below cell
        c.setFont("Helvetica", 6)
        c.setFillColorRGB(0.5, 0.5, 0.5)

        display_label = cell.char if cell.char.strip() else "SPC"
        # Always show variant number for consistency
        display_label = f"{display_label} ({cell.variant})"

        c.drawCentredString(x + CELL_SIZE / 2, y - CELL_SIZE - LABEL_HEIGHT + 1 * mm, display_label)
        c.setFillColorRGB(0, 0, 0)  # Reset fill

        # Light character hint in cell (very faint)
        if cell.char.strip():
            c.setFillColorRGB(0.92, 0.92, 0.92)
            c.setFont("Helvetica", 24)
            c.drawCentredString(x + CELL_SIZE / 2, y - CELL_SIZE + CELL_SIZE * 0.35, cell.char)
            c.setFillColorRGB(0, 0, 0)

    def _draw_alignment_markers(self, c: canvas.Canvas, page_w: float, page_h: float) -> None:
        """Draw filled square markers at all four corners."""
        c.setFillColorRGB(0, 0, 0)
        positions = [
            (MARGIN_X, page_h - MARGIN_Y - MARKER_SIZE),  # Top-left
            (page_w - MARGIN_X - MARKER_SIZE, page_h - MARGIN_Y - MARKER_SIZE),  # Top-right
            (MARGIN_X, MARGIN_Y),  # Bottom-left
            (page_w - MARGIN_X - MARKER_SIZE, MARGIN_Y),  # Bottom-right
        ]
        for mx, my in positions:
            c.rect(mx, my, MARKER_SIZE, MARKER_SIZE, fill=1)

    def _draw_qr_code(self, c: canvas.Canvas, page: PageSpec, page_w: float, page_h: float) -> None:
        """Draw QR code with worksheet metadata."""
        metadata = self.config.to_metadata()
        metadata["page"] = page.page_number
        metadata["total_pages"] = len(self.config.build_pages())
        metadata["cell_count"] = len(page.cells)

        # Build cell map for this page
        cell_map = [{"c": cell.char, "v": cell.variant, "l": cell.label} for cell in page.cells]
        metadata["cells"] = cell_map

        qr = qrcode.QRCode(
            version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10
        )
        qr.add_data(json.dumps(metadata, separators=(",", ":")))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes and draw
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        from reportlab.lib.utils import ImageReader

        qr_x = page_w - MARGIN_X - MARKER_SIZE - QR_SIZE - 5 * mm
        qr_y = page_h - MARGIN_Y - QR_SIZE - 2 * mm
        c.drawImage(ImageReader(img_buffer), qr_x, qr_y, QR_SIZE, QR_SIZE)

        # QR label
        c.setFont("Helvetica", 5)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(qr_x + QR_SIZE / 2, qr_y - 3 * mm, f"Page {page.page_number} metadata")
        c.setFillColorRGB(0, 0, 0)
