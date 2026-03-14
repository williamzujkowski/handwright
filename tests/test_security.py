"""Security tests for path traversal guards and file content validation."""

from __future__ import annotations

import io

import pytest
from httpx import ASGITransport, AsyncClient

from web.api.main import app, limiter


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset rate limiter storage between tests."""
    limiter.reset()


@pytest.mark.asyncio
async def test_upload_rejects_non_image_content() -> None:
    """Uploading a .png file with non-PNG content should be rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_content = b"This is not a PNG file at all"
        resp = await client.post(
            "/api/upload",
            files={"file": ("fake.png", io.BytesIO(fake_content), "image/png")},
        )
    assert resp.status_code == 422
    assert "does not match" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_pdf_with_wrong_content() -> None:
    """Uploading a .pdf file with non-PDF content should be rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_content = b"<html>not a pdf</html>"
        resp = await client.post(
            "/api/upload",
            files={"file": ("fake.pdf", io.BytesIO(fake_content), "application/pdf")},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_accepts_valid_png() -> None:
    """Uploading a valid PNG should succeed."""
    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), "white")
    img.save(buf, format="PNG")
    buf.seek(0)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/upload",
            files={"file": ("test.png", buf, "image/png")},
        )
    assert resp.status_code == 200
    assert "session_id" in resp.json()


@pytest.mark.asyncio
async def test_glyph_image_path_traversal_returns_404() -> None:
    """Requesting a glyph image with path traversal should not serve arbitrary files."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/glyphs/a" * 32 + "/images/../../etc/passwd")
    # Should return 400 (invalid path) or 404 (not found), never serve the file
    assert resp.status_code in (400, 404)


@pytest.mark.asyncio
async def test_render_image_path_traversal_returns_404() -> None:
    """Requesting a render with path traversal should not serve arbitrary files."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/renders/../../etc/passwd")
    assert resp.status_code in (400, 404)


@pytest.mark.asyncio
async def test_font_file_path_traversal_returns_404() -> None:
    """Requesting a font file with path traversal should not serve arbitrary files."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/fonts/../../etc/passwd")
    assert resp.status_code in (400, 404)
