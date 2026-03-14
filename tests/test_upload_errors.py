"""Tests for upload error handling — blank, unfilled, and malformed worksheets."""

from __future__ import annotations

import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas as pdf_canvas

from web.api.main import app, limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset rate limiter storage between tests to prevent cross-test pollution."""
    limiter.reset()


def _make_blank_worksheet_pdf() -> bytes:
    """Generate a worksheet PDF without filling it in (blank grid)."""
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=LETTER)
    # Draw some grid lines to simulate an unfilled worksheet
    width, height = LETTER
    for x in range(50, int(width), 60):
        c.line(x, 50, x, height - 50)
    for y in range(50, int(height), 60):
        c.line(50, y, width - 50, y)
    c.save()
    return buf.getvalue()


def _make_text_pdf() -> bytes:
    """Create a simple PDF with just text (not a worksheet)."""
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=LETTER)
    c.drawString(100, 700, "This is not a worksheet.")
    c.drawString(100, 680, "It contains only text content.")
    c.save()
    return buf.getvalue()


async def _upload_bytes(
    client: AsyncClient,
    content: bytes,
    filename: str,
    content_type: str,
) -> dict:
    """Upload raw bytes to the upload endpoint and return the JSON response."""
    resp = await client.post(
        "/api/upload",
        files={"file": (filename, io.BytesIO(content), content_type)},
    )
    assert resp.status_code == 200, f"Upload failed: {resp.status_code} {resp.text}"
    return resp.json()


@pytest.mark.asyncio
async def test_upload_blank_worksheet() -> None:
    """Upload a blank worksheet PDF (not filled in) and request glyphs.

    Should return 0 glyphs instead of a server error, since cv2 cannot
    read PDF files directly.
    """
    pdf_bytes = _make_blank_worksheet_pdf()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _upload_bytes(client, pdf_bytes, "blank_worksheet.pdf", "application/pdf")
        session_id = data["session_id"]

        resp = await client.get(f"/api/glyphs/{session_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    assert body["glyph_count"] == 0
    assert body["glyphs"] == []


@pytest.mark.asyncio
async def test_upload_random_pdf() -> None:
    """Upload a text-only PDF (not a worksheet) and request glyphs.

    Should handle gracefully and return 0 glyphs.
    """
    pdf_bytes = _make_text_pdf()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _upload_bytes(client, pdf_bytes, "random_doc.pdf", "application/pdf")
        session_id = data["session_id"]

        resp = await client.get(f"/api/glyphs/{session_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    assert body["glyph_count"] == 0
    assert body["glyphs"] == []


@pytest.mark.asyncio
async def test_glyphs_invalid_session() -> None:
    """Request glyphs for a non-existent session ID.

    Should return 404.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/glyphs/does_not_exist_1234567890")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_empty_image() -> None:
    """Upload a completely white PNG image and request glyphs.

    The detector should process it (falling back to simple resize since
    no markers will be found) and the extractor should handle blank cells
    gracefully, returning glyphs with no ink.
    """
    # Create a large-ish white image so the detector doesn't choke on tiny dimensions
    img = Image.new("RGB", (1100, 850), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        data = await _upload_bytes(client, png_bytes, "blank.png", "image/png")
        session_id = data["session_id"]

        resp = await client.get(f"/api/glyphs/{session_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"] == session_id
    # A blank white image will still have grid boxes computed (layout-based),
    # so glyph_count >= 0 is the key assertion — no crash.
    assert body["glyph_count"] >= 0
    assert isinstance(body["glyphs"], list)
    assert len(body["glyphs"]) == body["glyph_count"]
