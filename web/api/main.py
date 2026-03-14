"""Handwright API — FastAPI backend for handwriting font generation."""

import asyncio
import logging
import shutil
import tempfile
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from engine.fontgen.builder import FontBuilder, FontMetadata
from engine.glyphs.extractor import GlyphExtractor
from engine.renderer.handwriting import HandwritingRenderer, RenderOptions
from engine.segmentation.detector import WorksheetDetector
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

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

_UPLOAD_SIZE_LIMIT_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".heic"}
_UPLOADS_DIR = Path(tempfile.gettempdir()) / "handwright" / "uploads"
_OUTPUTS_DIR = Path(tempfile.gettempdir()) / "handwright" / "outputs"
_SESSION_MAX_AGE_SECONDS = 3600  # 1 hour

# Magic bytes for file content validation
_MAGIC_BYTES: dict[str, list[bytes]] = {
    ".png": [b"\x89PNG"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".pdf": [b"%PDF"],
    ".heic": [b"\x00\x00\x00", b"ftypheic", b"ftypmif1"],
}

logger = logging.getLogger("handwright")

limiter = Limiter(key_func=get_remote_address)


async def _cleanup_old_sessions() -> None:
    """Remove upload sessions older than _SESSION_MAX_AGE_SECONDS."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        now = time.time()
        for base_dir in [_UPLOADS_DIR, _OUTPUTS_DIR]:
            if not base_dir.exists():
                continue
            for item in base_dir.iterdir():
                try:
                    age = now - item.stat().st_mtime
                    if age > _SESSION_MAX_AGE_SECONDS:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)
                        logger.info("Cleaned up expired session artifact: %s", item.name)
                except OSError:
                    pass


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: start background tasks on startup."""
    cleanup_task = asyncio.create_task(_cleanup_old_sessions())
    yield
    cleanup_task.cancel()


app = FastAPI(
    title="Handwright API",
    version="0.1.0",
    description="Backend API for the Handwright handwriting-font generation service.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_magic_bytes(content: bytes, extension: str) -> bool:
    """Check that file content matches expected magic bytes for the extension."""
    signatures = _MAGIC_BYTES.get(extension, [])
    if not signatures:
        return True  # No validation available for this extension
    return any(content[: len(sig)] == sig for sig in signatures)


def _safe_resolve(base: Path, *parts: str) -> Path:
    """Resolve a path ensuring it stays within the base directory."""
    resolved = (base / Path(*parts)).resolve()
    base_resolved = base.resolve()
    if not str(resolved).startswith(str(base_resolved) + "/") and resolved != base_resolved:
        raise HTTPException(status_code=400, detail="Invalid path.")
    return resolved


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

    text: str = Field(min_length=1, max_length=50000)
    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    font_size: int = Field(default=48, ge=8, le=200)
    line_spacing: float = Field(default=1.5, ge=0.5, le=5.0)
    format: str = Field(default="png", pattern=r"^(png|pdf)$")


class RenderResponse(BaseModel):
    """Response returned after rendering."""

    image_url: str
    width: int
    height: int


class FontGenerateRequest(BaseModel):
    """Payload for font generation."""

    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    family_name: str = Field(min_length=1, max_length=100)
    designer: str = Field(default="", max_length=200)


class FontGenerateResponse(BaseModel):
    """Response returned after font generation."""

    download_url: str
    woff2_url: str
    css_snippet: str
    glyph_count: int
    variant_count: int


# ---------------------------------------------------------------------------
# Routes — Worksheet
# ---------------------------------------------------------------------------


@app.post("/api/worksheet/generate", tags=["worksheet"])
@limiter.limit("30/minute")
async def generate_worksheet(request: Request, include_symbols: bool = False) -> FileResponse:
    """Generate the complete handwriting worksheet PDF.

    Returns a downloadable PDF with all character cells, alignment markers,
    and QR metadata for automated glyph extraction.

    Args:
        include_symbols: Include extended symbols (@#$%^*+=[] etc.) on additional pages.
    """
    _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _OUTPUTS_DIR / f"worksheet_{uuid.uuid4().hex[:8]}.pdf"

    config = WorksheetConfig(include_symbols=include_symbols)
    generator = WorksheetGenerator(config)
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
@limiter.limit("10/minute")
async def upload_image(request: Request, file: UploadFile = File(...)) -> dict[str, str]:  # noqa: B008
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

    # Read and validate content
    content = await file.read()
    if not _validate_magic_bytes(content, suffix):
        raise HTTPException(
            status_code=422,
            detail=f"File content does not match expected format for '{suffix}'.",
        )

    # Create session
    session_id = uuid.uuid4().hex
    session_dir = _UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    upload_path = session_dir / f"original{suffix}"
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
    file_ext = ""
    for ext in [".png", ".jpg", ".jpeg", ".pdf", ".heic"]:
        candidate = session_dir / f"original{ext}"
        if candidate.exists():
            image_path = candidate
            file_ext = ext
            break

    if image_path is None:
        raise HTTPException(status_code=404, detail="No uploaded image found for this session.")

    # PDF files can't be processed by the image pipeline
    if file_ext == ".pdf":
        return {
            "session_id": session_id,
            "glyph_count": 0,
            "glyphs": [],
            "detail": (
                "PDF files cannot be processed directly by the image pipeline. "
                "Please print the worksheet, fill it in with dark ink, then photograph "
                "or scan the completed pages and upload the image (PNG or JPG)."
            ),
        }

    # Run detection + extraction pipeline (CPU-bound, offload to thread pool)
    glyphs_dir = session_dir / "glyphs"
    loop = asyncio.get_event_loop()

    detector = WorksheetDetector()
    try:
        result = await loop.run_in_executor(None, detector.detect, image_path)
    except (ValueError, FileNotFoundError) as exc:
        logger.warning("Detection failed for session %s: %s", session_id, exc)
        return {
            "session_id": session_id,
            "glyph_count": 0,
            "glyphs": [],
            "detail": (
                "Could not detect worksheet cells in the uploaded image. "
                "Make sure the image is well-lit, flat, and shows the full worksheet page."
            ),
        }

    if not result.boxes:
        return {
            "session_id": session_id,
            "glyph_count": 0,
            "glyphs": [],
            "detail": (
                "No character cells detected. Ensure you uploaded a photo of a filled-in "
                "worksheet (not the blank PDF). The image should be well-lit and show "
                "the full page with alignment markers visible in the corners."
            ),
        }

    extractor = GlyphExtractor()
    try:
        glyphs = await loop.run_in_executor(
            None,
            extractor.extract,
            result.corrected_image_path or image_path,
            result.boxes,
            glyphs_dir,
            result.cell_labels if result.cell_labels else None,
        )
    except (ValueError, FileNotFoundError, cv2.error) as exc:
        logger.warning("Extraction failed for session %s: %s", session_id, exc)
        return {
            "session_id": session_id,
            "glyph_count": 0,
            "glyphs": [],
            "detail": (
                "Glyph extraction failed. Try re-scanning with better lighting "
                "and ensure each character is written clearly with dark ink."
            ),
        }

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
    safe_name = Path(filename).name
    image_path = _safe_resolve(_UPLOADS_DIR, session_id, "glyphs", safe_name)

    if not image_path.exists() or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Glyph image not found.")

    return FileResponse(path=str(image_path), media_type="image/png")


# ---------------------------------------------------------------------------
# Routes — Render
# ---------------------------------------------------------------------------


@app.post("/api/render", response_model=RenderResponse, tags=["render"])
@limiter.limit("30/minute")
async def render_text(request: Request, body: RenderRequest) -> RenderResponse:
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
    render_id = uuid.uuid4().hex[:8]

    options = RenderOptions(
        font_path=font_path,
        font_size=body.font_size,
        line_spacing=body.line_spacing,
    )

    renderer = HandwritingRenderer()
    loop = asyncio.get_event_loop()

    if body.format == "pdf":
        output_path = _OUTPUTS_DIR / f"render_{render_id}.pdf"
        _, width, height = await loop.run_in_executor(
            None, renderer.render_pdf, body.text, options, output_path
        )
    else:
        output_path = _OUTPUTS_DIR / f"render_{render_id}.png"
        await loop.run_in_executor(None, renderer.render, body.text, options, output_path)
        from PIL import Image as PILImage

        img = PILImage.open(output_path)
        width, height = img.width, img.height
        img.close()

    return RenderResponse(
        image_url=f"/api/renders/{output_path.name}",
        width=width,
        height=height,
    )


# ---------------------------------------------------------------------------
# Routes — Font
# ---------------------------------------------------------------------------


@app.post("/api/font/generate", response_model=FontGenerateResponse, tags=["font"])
@limiter.limit("30/minute")
async def generate_font(request: Request, body: FontGenerateRequest) -> FontGenerateResponse:
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
    # Build the expected character order (same as worksheet generator)
    char_order: list[str] = []
    for char in LOWERCASE:
        for _ in range(LOWERCASE_VARIANTS):
            char_order.append(char)
    for char in UPPERCASE:
        for _ in range(UPPERCASE_VARIANTS):
            char_order.append(char)
    for char in DIGITS:
        for _ in range(DIGIT_VARIANTS):
            char_order.append(char)
    for char in PUNCTUATION:
        for _ in range(PUNCTUATION_VARIANTS):
            char_order.append(char)
    char_order.append(" ")

    glyph_map: dict[str, list[Path]] = {}
    glyph_files = sorted(glyphs_dir.glob("*.png"))

    for i, png in enumerate(glyph_files):
        parts = png.stem.split("_", 1)
        if len(parts) < 2:
            continue
        label = parts[1]

        # Try to extract character from label (e.g., "a_1" -> "a")
        char = label.split("_")[0] if "_" in label else label

        # If label is a fallback like "cell_0", use index to look up character
        if len(char) > 1 and i < len(char_order):
            char = char_order[i]

        # Collect all variants for each character
        if char and len(char) == 1:
            glyph_map.setdefault(char, []).append(png)

    if not glyph_map:
        raise HTTPException(
            status_code=400, detail="No valid glyphs could be mapped to characters."
        )

    _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    font_path = _OUTPUTS_DIR / f"{body.session_id}.ttf"

    meta = FontMetadata(
        family_name=body.family_name,
        designer=body.designer,
    )

    builder = FontBuilder()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: builder.build_ttf(glyph_map, font_path, metadata=meta))

    woff2_path = _OUTPUTS_DIR / f"{body.session_id}.woff2"
    await loop.run_in_executor(None, builder.build_woff2, font_path, woff2_path)

    ttf_url = f"/api/fonts/{body.session_id}.ttf"
    woff2_url = f"/api/fonts/{body.session_id}.woff2"
    css_snippet = (
        f"@font-face {{\n"
        f"  font-family: '{body.family_name}';\n"
        f"  src: url('{woff2_url}') format('woff2'),\n"
        f"       url('{ttf_url}') format('truetype');\n"
        f"}}"
    )

    total_variants = sum(len(paths) for paths in glyph_map.values())
    return FontGenerateResponse(
        download_url=ttf_url,
        woff2_url=woff2_url,
        css_snippet=css_snippet,
        glyph_count=len(glyph_map),
        variant_count=total_variants,
    )


# ---------------------------------------------------------------------------
# Routes — Static file serving
# ---------------------------------------------------------------------------


@app.get("/api/renders/{filename}", tags=["render"])
async def get_render_image(filename: str) -> FileResponse:
    """Serve a rendered handwriting image or PDF."""
    safe_name = Path(filename).name
    path = _safe_resolve(_OUTPUTS_DIR, safe_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Render not found.")
    media_type = "application/pdf" if safe_name.endswith(".pdf") else "image/png"
    return FileResponse(path=str(path), media_type=media_type)


@app.get("/api/fonts/{filename}", tags=["font"])
async def get_font_file(filename: str) -> FileResponse:
    """Serve a generated font file (.ttf or .woff2)."""
    safe_name = Path(filename).name
    path = _safe_resolve(_OUTPUTS_DIR, safe_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Font not found.")
    media_type = "font/woff2" if safe_name.endswith(".woff2") else "font/ttf"
    return FileResponse(
        path=str(path),
        media_type=media_type,
        filename=safe_name,
    )
