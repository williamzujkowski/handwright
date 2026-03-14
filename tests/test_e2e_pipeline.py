"""End-to-end integration test for the full Handwright pipeline.

Exercises: worksheet generation -> upload -> glyph extraction ->
font generation -> text rendering.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from web.api.main import app


@pytest.mark.asyncio
async def test_full_pipeline_end_to_end(tmp_path: Path) -> None:
    """Run the complete pipeline from worksheet to rendered text."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Generate worksheet PDF
        worksheet_resp = await client.post("/api/worksheet/generate")
        assert worksheet_resp.status_code == 200
        assert worksheet_resp.content[:5] == b"%PDF-"

        # Step 2: Upload a worksheet-like image
        # Create a landscape image simulating a scanned worksheet
        img = Image.new("RGB", (1100, 850), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("scan.png", buf, "image/png")},
        )
        assert upload_resp.status_code == 200
        session_id = upload_resp.json()["session_id"]
        assert len(session_id) > 0

        # Step 3: Extract glyphs
        glyphs_resp = await client.get(f"/api/glyphs/{session_id}")
        assert glyphs_resp.status_code == 200
        glyphs_data = glyphs_resp.json()
        assert glyphs_data["glyph_count"] > 0
        assert len(glyphs_data["glyphs"]) > 0

        # Verify glyph images are accessible
        first_glyph = glyphs_data["glyphs"][0]
        assert "image_url" in first_glyph
        assert "label" in first_glyph

        img_resp = await client.get(first_glyph["image_url"])
        assert img_resp.status_code == 200

        # Step 4: Generate font
        font_resp = await client.post(
            "/api/font/generate",
            json={
                "session_id": session_id,
                "family_name": "Test Handwriting",
                "designer": "Integration Test",
            },
        )
        assert font_resp.status_code == 200
        font_data = font_resp.json()
        assert font_data["glyph_count"] > 0
        assert "download_url" in font_data

        # Verify font is downloadable
        font_file_resp = await client.get(font_data["download_url"])
        assert font_file_resp.status_code == 200

        # Step 5: Render text
        render_resp = await client.post(
            "/api/render",
            json={
                "text": "Hello World",
                "session_id": session_id,
                "font_size": 48,
                "line_spacing": 1.5,
            },
        )
        assert render_resp.status_code == 200
        render_data = render_resp.json()
        assert render_data["width"] > 0
        assert render_data["height"] > 0
        assert "image_url" in render_data

        # Verify rendered image is accessible
        render_img_resp = await client.get(render_data["image_url"])
        assert render_img_resp.status_code == 200


@pytest.mark.asyncio
async def test_pipeline_error_handling() -> None:
    """Verify proper error responses for invalid pipeline states."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Render without generating font first
        render_resp = await client.post(
            "/api/render",
            json={
                "text": "Hello",
                "session_id": "nonexistent",
                "font_size": 48,
                "line_spacing": 1.5,
            },
        )
        assert render_resp.status_code == 404

        # Generate font without extracting glyphs first
        font_resp = await client.post(
            "/api/font/generate",
            json={
                "session_id": "nonexistent",
                "family_name": "Test",
            },
        )
        assert font_resp.status_code == 404
