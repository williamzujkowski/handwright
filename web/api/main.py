"""Handwright API — FastAPI backend for handwriting font generation."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from engine.fontgen.builder import FontBuilder, FontMetadata
from engine.glyphs.extractor import GlyphExtractor
from engine.renderer.handwriting import HandwritingRenderer, RenderOptions
from engine.segmentation.detector import WorksheetDetector
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
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:  # noqa: B008
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

    # Find the uploaded image
    image_path = None
    for ext in [".png", ".jpg", ".jpeg", ".pdf", ".heic"]:
        candidate = session_dir / f"original{ext}"
        if candidate.exists():
            image_path = candidate
            break

    if image_path is None:
        raise HTTPException(status_code=404, detail="No uploaded image found for this session.")

    # Run detection + extraction pipeline
    glyphs_dir = session_dir / "glyphs"

    detector = WorksheetDetector()
    result = detector.detect(image_path)

    extractor = GlyphExtractor()
    glyphs = extractor.extract(
        result.corrected_image_path or image_path,
        result.boxes,
        glyphs_dir,
        result.cell_labels if result.cell_labels else None,
    )

    return {
        "session_id": session_id,
        "glyph_count": len(glyphs),
        "glyphs": [
            {
                "label": g.label,
                "image_url": f"/api/glyphs/{session_id}/images/{g.image_path.name}",
                "width": g.width,
                "height": g.height,
            }
            for g in glyphs
        ],
    }


@app.get("/api/glyphs/{session_id}/images/{filename}", tags=["glyphs"])
async def get_glyph_image(session_id: str, filename: str) -> FileResponse:
    """Serve an individual extracted glyph image.

    Raises:
        404: If session or glyph image not found.
    """
    # Sanitize filename to prevent path traversal
    safe_name = Path(filename).name
    image_path = _UPLOADS_DIR / session_id / "glyphs" / safe_name

    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Glyph image not found.")

    return FileResponse(path=str(image_path), media_type="image/png")


# ---------------------------------------------------------------------------
# Routes — Render
# ---------------------------------------------------------------------------


@app.post("/api/render", response_model=RenderResponse, tags=["render"])
async def render_text(body: RenderRequest) -> RenderResponse:
    """Render arbitrary text using handwriting glyphs.

    Raises:
        404: If session_id is not recognised.
    """
    # Check session and find font
    session_dir = _UPLOADS_DIR / body.session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session '{body.session_id}' not found.")

    font_path = _OUTPUTS_DIR / f"{body.session_id}.ttf"
    if not font_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Font not yet generated for this session. Call /api/font/generate first.",
        )

    _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _OUTPUTS_DIR / f"render_{uuid.uuid4().hex[:8]}.png"

    options = RenderOptions(
        font_path=font_path,
        font_size=body.font_size,
        line_spacing=body.line_spacing,
    )

    renderer = HandwritingRenderer()
    renderer.render(body.text, options, output_path)

    from PIL import Image as PILImage

    img = PILImage.open(output_path)
    return RenderResponse(
        image_url=f"/api/renders/{output_path.name}",
        width=img.width,
        height=img.height,
    )


# ---------------------------------------------------------------------------
# Routes — Font
# ---------------------------------------------------------------------------


@app.post("/api/font/generate", response_model=FontGenerateResponse, tags=["font"])
async def generate_font(body: FontGenerateRequest) -> FontGenerateResponse:
    """Build a downloadable .ttf font from extracted glyphs.

    Raises:
        404: If session_id is not recognised.
    """
    session_dir = _UPLOADS_DIR / body.session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session '{body.session_id}' not found.")

    glyphs_dir = session_dir / "glyphs"
    if not glyphs_dir.exists() or not any(glyphs_dir.iterdir()):
        raise HTTPException(
            status_code=400,
            detail="No glyphs found. Call /api/glyphs/{session_id} first to extract glyphs.",
        )

    # Build glyph map: character -> image path
    # Glyph files are named like "0001_a_1.png" — extract the character from the label
    glyph_map: dict[str, Path] = {}
    for png in sorted(glyphs_dir.glob("*.png")):
        # Label is between first underscore and last underscore
        parts = png.stem.split("_", 1)
        if len(parts) < 2:
            continue
        label = parts[1]
        # For variant labels like "a_1", take the first character
        char = label.split("_")[0] if "_" in label else label
        # Only take the first variant of each character
        if char and len(char) == 1 and char not in glyph_map:
            glyph_map[char] = png

    if not glyph_map:
        raise HTTPException(status_code=400, detail="No valid glyphs could be mapped to characters.")

    _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    font_path = _OUTPUTS_DIR / f"{body.session_id}.ttf"

    meta = FontMetadata(
        family_name=body.family_name,
        designer=body.designer,
    )

    builder = FontBuilder()
    builder.build_ttf(glyph_map, font_path, metadata=meta)

    return FontGenerateResponse(
        download_url=f"/api/fonts/{body.session_id}.ttf",
        glyph_count=len(glyph_map),
    )


# ---------------------------------------------------------------------------
# Routes — Static file serving
# ---------------------------------------------------------------------------


@app.get("/api/renders/{filename}", tags=["render"])
async def get_render_image(filename: str) -> FileResponse:
    """Serve a rendered handwriting image."""
    safe_name = Path(filename).name
    path = _OUTPUTS_DIR / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Render not found.")
    return FileResponse(path=str(path), media_type="image/png")


@app.get("/api/fonts/{filename}", tags=["font"])
async def get_font_file(filename: str) -> FileResponse:
    """Serve a generated font file."""
    safe_name = Path(filename).name
    path = _OUTPUTS_DIR / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Font not found.")
    return FileResponse(
        path=str(path),
        media_type="font/ttf",
        filename=safe_name,
    )
