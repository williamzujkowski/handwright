"""Tests for API input validation (Field constraints on request models)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from web.api.main import app, limiter


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset rate limiter storage between tests to prevent cross-test pollution."""
    limiter.reset()


VALID_SESSION_ID = "a" * 32  # valid 32-char hex string


@pytest.mark.asyncio
async def test_render_empty_text_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/render",
            json={"text": "", "session_id": VALID_SESSION_ID},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_render_text_too_long_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/render",
            json={"text": "x" * 50001, "session_id": VALID_SESSION_ID},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_render_font_size_too_small_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/render",
            json={
                "text": "hello",
                "session_id": VALID_SESSION_ID,
                "font_size": 1,
            },
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_render_font_size_too_large_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/render",
            json={
                "text": "hello",
                "session_id": VALID_SESSION_ID,
                "font_size": 999,
            },
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_render_invalid_session_id_format_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/render",
            json={"text": "hello", "session_id": "../../etc/passwd"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_render_line_spacing_out_of_range_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/render",
            json={
                "text": "hello",
                "session_id": VALID_SESSION_ID,
                "line_spacing": 10.0,
            },
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_font_generate_empty_family_name_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/font/generate",
            json={"session_id": VALID_SESSION_ID, "family_name": ""},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_font_generate_invalid_session_id_returns_422() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/font/generate",
            json={"session_id": "not-valid-hex!", "family_name": "MyFont"},
        )
    assert resp.status_code == 422
