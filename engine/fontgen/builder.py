from __future__ import annotations

from pathlib import Path


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
        pass
