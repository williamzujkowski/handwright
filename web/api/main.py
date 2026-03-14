"""Handwright API — FastAPI backend for handwriting font generation."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from engine.worksheet.generator import WorksheetGenerator

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

_UPLOAD_SIZE_LIMIT_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".heic"}
_UPLOADS_DIR = Path(tempfile.gettempdir()) / "handwright" / "uploads"
_OUTPUTS_DIR = Path(tempfile.gettempdir()) / "handwright" / "outputs"

app = FastAPI(
    title="Handwright API",
    version="0.1.0",
    description="Backend API for the Handwright handwriting-font generation service.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def enforce_upload_size_limit(request: Request, call_next: object) -> object:
    """Reject requests whose Content-Length exceeds the configured upload limit."""
    content_length = request.headers.get("content-length")
    if content_length is not None and int(content_length) > _UPLOAD_SIZE_LIMIT_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body exceeds the 10 MB upload limit."},
        )
    return await call_next(request)  # type: ignore[operator]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Return service liveness status."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class RenderRequest(BaseModel):
    """Payload for handwriting rendering."""

    text: str
    session_id: str
    font_size: int = 48
    line_spacing: float = 1.5


class RenderResponse(BaseModel):
    """Response returned after rendering."""

    image_url: str
    width: int
    height: int


class FontGenerateRequest(BaseModel):
    """Payload for font generation."""

    session_id: str
    family_name: str
    designer: str = ""


class FontGenerateResponse(BaseModel):
    """Response returned after font generation."""

    download_url: str
    glyph_count: int


# ---------------------------------------------------------------------------
# Routes — Worksheet
# ---------------------------------------------------------------------------


@app.post("/api/worksheet/generate", tags=["worksheet"])
async def generate_worksheet() -> FileResponse:
    """Generate the complete handwriting worksheet PDF.

    Returns a downloadable PDF with all character cells, alignment markers,
    and QR metadata for automated glyph extraction.
    """
    _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _OUTPUTS_DIR / f"worksheet_{uuid.uuid4().hex[:8]}.pdf"

    generator = WorksheetGenerator()
    generator.generate_pdf(output_path)

    return FileResponse(
        path=str(output_path),
        media_type="application/pdf",
        filename="handwright_worksheet.pdf",
    )


# ---------------------------------------------------------------------------
# Routes — Upload
# ---------------------------------------------------------------------------


@app.post("/api/upload", tags=["upload"])
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    """Accept a handwriting image upload and begin processing.

    Returns a session_id for subsequent glyph extraction calls.

    Raises:
        413: If the file exceeds the 10 MB upload limit.
        422: If the uploaded file is not a supported image format.
    """
    # Validate file extension
    filename = file.filename or "unknown"
    suffix = Path(filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file format '{suffix}'. Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    # Create session
    session_id = uuid.uuid4().hex
    session_dir = _UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    upload_path = session_dir / f"original{suffix}"
    content = await file.read()
    upload_path.write_bytes(content)

    return {"session_id": session_id, "filename": filename, "size_bytes": str(len(content))}


# ---------------------------------------------------------------------------
# Routes — Glyphs
# ---------------------------------------------------------------------------


@app.get("/api/glyphs/{session_id}", tags=["glyphs"])
async def get_glyphs(session_id: str) -> dict[str, object]:
    """Return the extracted glyphs for an upload session.

    Raises:
        404: If session_id is not recognised.
    """
    session_dir = _UPLOADS_DIR / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    # TODO: Implement glyph extraction pipeline (Milestone 2)
    raise HTTPException(status_code=501, detail="Glyph extraction not yet implemented.")


# ---------------------------------------------------------------------------
# Routes — Render
# ---------------------------------------------------------------------------


@app.post("/api/render", response_model=RenderResponse, tags=["render"])
async def render_text(body: RenderRequest) -> RenderResponse:
    """Render arbitrary text using handwriting glyphs.

    Raises:
        404: If session_id is not recognised.
    """
    # TODO: Implement handwriting renderer (Milestone 4)
    raise HTTPException(status_code=501, detail="Rendering not yet implemented.")


# ---------------------------------------------------------------------------
# Routes — Font
# ---------------------------------------------------------------------------


@app.post("/api/font/generate", response_model=FontGenerateResponse, tags=["font"])
async def generate_font(body: FontGenerateRequest) -> FontGenerateResponse:
    """Build a downloadable .ttf font from extracted glyphs.

    Raises:
        404: If session_id is not recognised.
    """
    # TODO: Implement font generation (Milestone 5)
    raise HTTPException(status_code=501, detail="Font generation not yet implemented.")
