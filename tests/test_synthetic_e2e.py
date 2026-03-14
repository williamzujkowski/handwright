"""E2E pipeline test using synthetic handwriting fixtures.

Exercises the full pipeline with realistic character content:
synthetic worksheet → upload → detect → extract → font build → render.

Unlike test_e2e_pipeline.py (which uses a blank white image), this test
validates that the extracted glyphs contain actual ink and that the generated
font has usable character outlines.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from web.api.main import app, limiter

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "synthetic_worksheet.png"


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset rate limiter storage between tests."""
    limiter.reset()


@pytest.mark.asyncio
async def test_synthetic_worksheet_full_pipeline() -> None:
    """Run the complete pipeline with a synthetic handwriting worksheet.

    Validates:
    - Glyph extraction produces non-empty glyphs
    - Font generation succeeds with real character data
    - Text rendering produces a non-trivial image
    """
    assert FIXTURE_PATH.exists(), f"Fixture not found: {FIXTURE_PATH}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Upload synthetic worksheet
        buf = io.BytesIO(FIXTURE_PATH.read_bytes())
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("synthetic_worksheet.png", buf, "image/png")},
        )
        assert upload_resp.status_code == 200
        session_id = upload_resp.json()["session_id"]
        assert len(session_id) == 32  # UUID hex format

        # Step 2: Extract glyphs
        glyphs_resp = await client.get(f"/api/glyphs/{session_id}")
        assert glyphs_resp.status_code == 200
        glyphs_data = glyphs_resp.json()
        assert glyphs_data["glyph_count"] > 0, "Should extract at least some glyphs"

        # Verify glyphs have actual content (not blank)
        first_glyph = glyphs_data["glyphs"][0]
        glyph_img_resp = await client.get(first_glyph["image_url"])
        assert glyph_img_resp.status_code == 200

        glyph_img = Image.open(io.BytesIO(glyph_img_resp.content))
        glyph_arr = np.array(glyph_img)
        if glyph_arr.shape[-1] == 4:  # RGBA
            assert glyph_arr[:, :, 3].max() > 0, "Glyph should have non-transparent pixels"
        else:
            assert glyph_arr.min() < 200, "Glyph should have dark (ink) pixels"

        # Step 3: Generate font
        font_resp = await client.post(
            "/api/font/generate",
            json={
                "session_id": session_id,
                "family_name": "Synthetic Test",
                "designer": "E2E Test",
            },
        )
        assert font_resp.status_code == 200
        font_data = font_resp.json()
        assert font_data["glyph_count"] > 0, "Font should contain glyphs"
        assert "download_url" in font_data
        assert "woff2_url" in font_data

        # Verify font files exist and have content
        ttf_resp = await client.get(font_data["download_url"])
        assert ttf_resp.status_code == 200
        assert len(ttf_resp.content) > 1000, "TTF file should have substantial content"

        woff2_resp = await client.get(font_data["woff2_url"])
        assert woff2_resp.status_code == 200
        assert woff2_resp.content[:4] == b"wOF2", "WOFF2 magic bytes"

        # Step 4: Render text using the generated font
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

        # Verify rendered image has actual content (not blank)
        render_img_resp = await client.get(render_data["image_url"])
        assert render_img_resp.status_code == 200

        render_img = Image.open(io.BytesIO(render_img_resp.content))
        render_arr = np.array(render_img)
        # The rendered image should have some non-white pixels (ink)
        if len(render_arr.shape) == 3 and render_arr.shape[-1] == 4:
            has_content = render_arr[:, :, 3].max() > 0
        else:
            has_content = render_arr.min() < 240
        assert has_content, "Rendered image should contain visible handwriting content"


@pytest.mark.asyncio
async def test_synthetic_glyph_extraction_quality() -> None:
    """Verify that glyph extraction from the synthetic worksheet produces
    a reasonable number of usable glyphs.
    """
    assert FIXTURE_PATH.exists()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        buf = io.BytesIO(FIXTURE_PATH.read_bytes())
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("synthetic.png", buf, "image/png")},
        )
        session_id = upload_resp.json()["session_id"]

        glyphs_resp = await client.get(f"/api/glyphs/{session_id}")
        glyphs_data = glyphs_resp.json()

        # With 32 cells on the synthetic worksheet, we should get at least 20 usable glyphs
        assert glyphs_data["glyph_count"] >= 20, (
            f"Expected at least 20 glyphs, got {glyphs_data['glyph_count']}"
        )

        # Check that extracted glyph images are valid PNGs
        for glyph in glyphs_data["glyphs"][:5]:
            resp = await client.get(glyph["image_url"])
            assert resp.status_code == 200
            img = Image.open(io.BytesIO(resp.content))
            assert img.size == (256, 256), "Glyph should be normalized to 256x256"
