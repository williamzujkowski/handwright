"""Tests for the FastAPI API endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from web.api.main import app, limiter


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset rate limiter storage between tests to prevent cross-test pollution."""
    limiter.reset()


@pytest.mark.asyncio
async def test_docs_returns_200() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/docs")

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_returns_ok() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_generate_worksheet_returns_pdf() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/worksheet/generate")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_generate_worksheet_pdf_magic_bytes() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/worksheet/generate")

    assert resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_upload_valid_png_returns_session_id(tmp_path: object) -> None:
    buf = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buf, format="PNG")
    buf.seek(0)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/upload",
            files={"file": ("test_image.png", buf, "image/png")},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0


@pytest.mark.asyncio
async def test_upload_invalid_extension_returns_422() -> None:
    buf = io.BytesIO(b"not a real file")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/upload",
            files={"file": ("document.txt", buf, "text/plain")},
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_glyphs_nonexistent_session_returns_404() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/glyphs/nonexistent_session_id_000")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upload_rate_limit_returns_429_after_10_requests() -> None:
    """Verify that the upload endpoint enforces a 10/minute rate limit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(10):
            buf = io.BytesIO()
            Image.new("RGB", (1, 1)).save(buf, format="PNG")
            buf.seek(0)
            resp = await client.post(
                "/api/upload",
                files={"file": ("test_image.png", buf, "image/png")},
            )
            assert resp.status_code == 200

        buf = io.BytesIO()
        Image.new("RGB", (1, 1)).save(buf, format="PNG")
        buf.seek(0)
        resp = await client.post(
            "/api/upload",
            files={"file": ("test_image.png", buf, "image/png")},
        )
        assert resp.status_code == 429


@pytest.mark.asyncio
async def test_get_glyphs_valid_session_extracts_glyphs() -> None:
    """Upload a worksheet-like image, then request glyphs."""
    # Create a larger image that the detector can process (simulated scan)
    img = Image.new("RGB", (1100, 850), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("scan.png", buf, "image/png")},
        )
        session_id = upload_resp.json()["session_id"]

        resp = await client.get(f"/api/glyphs/{session_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert "glyph_count" in data
    assert data["glyph_count"] > 0
    assert "glyphs" in data
    assert len(data["glyphs"]) == data["glyph_count"]
