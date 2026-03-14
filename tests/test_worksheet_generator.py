"""Tests for the worksheet generator."""

from __future__ import annotations

from pathlib import Path

from engine.worksheet.generator import (
    DIGIT_VARIANTS,
    DIGITS,
    LOWERCASE,
    LOWERCASE_VARIANTS,
    PUNCTUATION,
    PUNCTUATION_VARIANTS,
    UPPERCASE,
    UPPERCASE_VARIANTS,
    WorksheetConfig,
    WorksheetGenerator,
)


class TestWorksheetConfig:
    """Tests for WorksheetConfig."""

    def test_build_pages_returns_pages(self) -> None:
        config = WorksheetConfig()
        pages = config.build_pages()
        assert len(pages) > 0

    def test_total_cell_count(self) -> None:
        config = WorksheetConfig()
        pages = config.build_pages()
        total_cells = sum(len(p.cells) for p in pages)

        expected = (
            len(LOWERCASE) * LOWERCASE_VARIANTS
            + len(UPPERCASE) * UPPERCASE_VARIANTS
            + len(DIGITS) * DIGIT_VARIANTS
            + len(PUNCTUATION) * PUNCTUATION_VARIANTS
            + 1  # space
        )
        assert total_cells == expected

    def test_metadata_contains_required_keys(self) -> None:
        config = WorksheetConfig()
        meta = config.to_metadata()
        assert "v" in meta
        assert "cell_mm" in meta
        assert "cols" in meta
        assert "charset" in meta

    def test_page_numbers_sequential(self) -> None:
        config = WorksheetConfig()
        pages = config.build_pages()
        for i, page in enumerate(pages):
            assert page.page_number == i + 1


class TestWorksheetGenerator:
    """Tests for WorksheetGenerator."""

    def test_generate_pdf_creates_file(self, tmp_path: Path) -> None:
        generator = WorksheetGenerator()
        output = tmp_path / "test_worksheet.pdf"
        result = generator.generate_pdf(output)

        assert result.exists()
        assert result.suffix == ".pdf"
        assert result.stat().st_size > 0

    def test_generate_pdf_returns_resolved_path(self, tmp_path: Path) -> None:
        generator = WorksheetGenerator()
        output = tmp_path / "subdir" / "worksheet.pdf"
        result = generator.generate_pdf(output)

        assert result == output.resolve()
        assert result.exists()

    def test_generate_pdf_content_is_valid_pdf(self, tmp_path: Path) -> None:
        generator = WorksheetGenerator()
        output = tmp_path / "test.pdf"
        generator.generate_pdf(output)

        content = output.read_bytes()
        assert content[:5] == b"%PDF-"

    def test_generate_pdf_performance(self, tmp_path: Path) -> None:
        """Worksheet should generate in under 5 seconds."""
        import time

        generator = WorksheetGenerator()
        output = tmp_path / "perf_test.pdf"

        start = time.monotonic()
        generator.generate_pdf(output)
        elapsed = time.monotonic() - start

        assert elapsed < 5.0, f"Worksheet generation took {elapsed:.2f}s (target: <5s)"
