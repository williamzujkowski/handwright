from __future__ import annotations

from pathlib import Path

import cv2
from fontTools.fontBuilder import FontBuilder as FTFontBuilder


class FontMetadata:
    """Descriptive metadata embedded in the generated font file."""

    def __init__(
        self,
        family_name: str,
        style_name: str = "Regular",
        version: str = "1.0",
        designer: str = "",
    ) -> None:
        """Initialise font metadata.

        Args:
            family_name: Human-readable font family name (e.g. "My Handwriting").
            style_name: Style variant name (e.g. "Regular", "Bold").
            version: Font version string (e.g. "1.0").
            designer: Name of the person whose handwriting was captured.
        """
        self.family_name = family_name
        self.style_name = style_name
        self.version = version
        self.designer = designer


def _char_to_glyph_name(char: str) -> str:
    """Convert a character to a valid PostScript glyph name."""
    cp = ord(char)
    if char == " ":
        return "space"
    if "a" <= char <= "z" or "A" <= char <= "Z":
        return char
    if "0" <= char <= "9":
        return f"uni{cp:04X}"
    return f"uni{cp:04X}"


def _image_to_contours(
    image_path: Path,
    units_per_em: int,
    ascender: int,
) -> tuple[list[list[tuple[int, int]]], int]:
    """Load a glyph image and extract contours scaled to font units.

    Returns:
        A tuple of (contours, advance_width) where contours is a list of
        contour point lists and advance_width is the horizontal advance in
        font units.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    img_height, img_width = img.shape[:2]

    # Extract alpha channel or convert to grayscale
    if img.ndim == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
    elif img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        alpha = gray
    else:
        alpha = img

    # Threshold to binary
    _, binary = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)

    # Find contours
    contours_cv, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Scale factors: map image pixels to font units
    scale_x = units_per_em / img_width
    scale_y = ascender / img_height

    font_contours: list[list[tuple[int, int]]] = []
    for contour in contours_cv:
        # Simplify the contour
        epsilon = 0.005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) < 3:
            continue

        points: list[tuple[int, int]] = []
        for point in approx:
            px, py = point[0]
            # Scale to font units; flip Y axis (image Y goes down, font Y goes up)
            fx = int(round(px * scale_x))
            fy = int(round((img_height - py) * scale_y))
            points.append((fx, fy))

        font_contours.append(points)

    advance_width = units_per_em
    return font_contours, advance_width


class FontBuilder:
    """Assembles individual glyph images into a TrueType font file.

    Accepts a mapping of Unicode code points to glyph image paths and uses
    fonttools to construct a valid .ttf font that can be installed system-wide
    or embedded in documents.
    """

    def build_ttf(
        self,
        glyph_map: dict[str, Path],
        output_path: Path,
        metadata: FontMetadata | None = None,
        units_per_em: int = 1000,
    ) -> Path:
        """Build a TrueType font from a collection of glyph images.

        Args:
            glyph_map: Mapping of single-character strings to the corresponding
                       glyph PNG paths. Each PNG should have a transparent background.
            output_path: Destination path for the .ttf file.
            metadata: Optional font metadata to embed. Defaults are used when omitted.
            units_per_em: Font coordinate space size. Standard value is 1000.

        Returns:
            The resolved path of the written .ttf font file.

        Raises:
            ValueError: If *glyph_map* is empty.
            FileNotFoundError: If any glyph image path in *glyph_map* does not exist.
        """
        if not glyph_map:
            raise ValueError("glyph_map must not be empty")

        # Validate all image paths exist before doing any work
        for char, img_path in glyph_map.items():
            if not img_path.exists():
                raise FileNotFoundError(
                    f"Glyph image not found for '{char}': {img_path}"
                )

        if metadata is None:
            metadata = FontMetadata(family_name="Handwright")

        ascender = int(units_per_em * 0.8)
        descender = -(units_per_em - ascender)
        cap_height = int(units_per_em * 0.7)
        x_height = int(units_per_em * 0.5)

        # Build glyph names and character map
        glyph_names = [".notdef", "space"]
        char_map: dict[int, str] = {0x20: "space"}
        glyph_data: dict[str, list[list[tuple[int, int]]]] = {}
        advance_widths: dict[str, int] = {
            ".notdef": units_per_em // 2,
            "space": units_per_em // 4,
        }

        for char, img_path in sorted(glyph_map.items()):
            gname = _char_to_glyph_name(char)
            if gname not in glyph_names:
                glyph_names.append(gname)
            char_map[ord(char)] = gname

            contours, adv_w = _image_to_contours(img_path, units_per_em, ascender)
            glyph_data[gname] = contours
            advance_widths[gname] = adv_w

        # Create the font using fontTools.fontBuilder
        fb = FTFontBuilder(units_per_em, isTTF=True)
        fb.setupGlyphOrder(glyph_names)
        fb.setupCharacterMap(char_map)

        # Build glyf table data
        fb.setupGlyf(
            _build_glyf_dict(glyph_names, glyph_data, fb)
        )

        # Horizontal metrics: {glyph_name: (advance_width, lsb)}
        metrics: dict[str, tuple[int, int]] = {}
        for gname in glyph_names:
            adv = advance_widths.get(gname, units_per_em)
            metrics[gname] = (adv, 0)
        fb.setupHorizontalMetrics(metrics)

        fb.setupHorizontalHeader(
            ascent=ascender,
            descent=descender,
        )

        fb.setupNameTable(
            {
                "familyName": metadata.family_name,
                "styleName": metadata.style_name,
            },
        )

        fb.setupOS2(
            sTypoAscender=ascender,
            sTypoDescender=descender,
            sTypoLineGap=0,
            usWinAscent=ascender,
            usWinDescent=abs(descender),
            sxHeight=x_height,
            sCapHeight=cap_height,
        )

        fb.setupPost()
        fb.setupHead(unitsPerEm=units_per_em)

        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fb.font.save(str(output_path))

        return output_path


def _build_glyf_dict(
    glyph_names: list[str],
    glyph_data: dict[str, list[list[tuple[int, int]]]],
    fb: FTFontBuilder,
) -> dict[str, dict[str, object]]:
    """Build the glyf table dict for fontTools.fontBuilder.setupGlyf.

    Uses the pen API to draw contours into each glyph.
    """
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    glyph_table: dict[str, TTGlyphPen] = {}

    for gname in glyph_names:
        pen = TTGlyphPen(None)
        contours = glyph_data.get(gname)
        if contours:
            for contour in contours:
                if len(contour) < 3:
                    continue
                pen.moveTo(contour[0])
                for pt in contour[1:]:
                    pen.lineTo(pt)
                pen.closePath()
        else:
            # Empty glyph (.notdef, space, etc.)
            pass

        glyph_table[gname] = pen.glyph()

    return glyph_table
