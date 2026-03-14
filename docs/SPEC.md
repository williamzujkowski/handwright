# Handwright — Design Specification

**Version:** 0.1.0-draft
**Date:** 2026-03-13
**License:** MIT

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Design Goals](#2-design-goals)
3. [Non-Goals (v1)](#3-non-goals-v1)
4. [Character Set](#4-character-set)
5. [Worksheet Specification](#5-worksheet-specification)
6. [Glyph Extraction Pipeline](#6-glyph-extraction-pipeline)
7. [Glyph Variant System](#7-glyph-variant-system)
8. [Handwriting Renderer](#8-handwriting-renderer)
9. [Font Generation](#9-font-generation)
10. [Note and Card Generator](#10-note-and-card-generator)
11. [API Endpoints](#11-api-endpoints)
12. [Architecture](#12-architecture)
13. [Security](#13-security)
14. [Performance Targets](#14-performance-targets)
15. [Success Criteria](#15-success-criteria)
16. [Development Milestones](#16-development-milestones)

---

## 1. Project Overview

Handwright is an open-source web application that converts handwriting samples into custom fonts and handwritten-style notes. The user prints a structured worksheet, writes characters in the designated cells, scans or photographs the completed sheet, and uploads it. The engine extracts individual glyphs, normalizes them, and assembles them into a usable typeface and a rendering engine for producing handwritten-style text output.

**Core properties:**

- **Local-first:** all processing occurs on the user's own machine or self-hosted server; no data is sent to third-party services
- **Self-hostable:** ships as a Docker Compose stack; a single `docker compose up` command is the full deployment procedure
- **Privacy-preserving:** no accounts, no telemetry, no analytics; uploaded images are processed in memory and discarded
- **Open source:** MIT license; all code, models, and tooling are freely available and modifiable

---

## 2. Design Goals

### Primary Goals

| Goal | Description |
|---|---|
| Easy capture | The worksheet is printable on any A4 or US Letter printer. Completion requires only a pen and approximately 15 minutes. |
| Minimal effort | Upload one photo or scan. No manual cropping, cell identification, or alignment required. |
| Realistic output | Rendered text should be indistinguishable from casual handwriting to a casual observer at normal reading distance. |
| Self-hostable | One Docker Compose file, no external dependencies at runtime, runs on commodity hardware. |
| Open source | Full MIT license; contributions accepted via standard pull request workflow. |

### Secondary Goals

| Goal | Description |
|---|---|
| Optional font export | Generate a `.ttf` file for use in desktop applications, word processors, and design tools. |
| Printable note export | Render multi-page notes as PDF for printing or sharing. |
| Handwriting variability | Use multiple glyph samples to introduce natural variation so repeated characters do not look identical. |

---

## 3. Non-Goals (v1)

The following are explicitly out of scope for the initial release:

- **Signature cloning:** Handwright does not support capturing, reproducing, or exporting signatures. This is an ethical boundary, not a technical limitation.
- **Legal document simulation:** The project will not be marketed or architected for producing documents that simulate legal authenticity.
- **Freeform extraction:** Extracting glyphs from arbitrary handwritten text (rather than a structured worksheet) is not supported.
- **Multilingual character sets:** Only the English character set (A-Z, a-z, 0-9, common punctuation) is supported. CJK, Arabic, Devanagari, and other scripts are deferred.
- **ML training pipelines:** Handwright does not train machine learning models and does not expose user data for any training purpose.
- **Animation or motion:** No animated handwriting effects are in scope.

---

## 4. Character Set

English only. The worksheet captures the following characters:

### Lowercase (3 samples each)

```
a b c d e f g h i j k l m n o p q r s t u v w x y z
```

26 characters × 3 samples = **78 glyphs**

### Uppercase (2 samples each)

```
A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
```

26 characters × 2 samples = **52 glyphs**

### Digits (2 samples each)

```
0 1 2 3 4 5 6 7 8 9
```

10 characters × 2 samples = **20 glyphs**

### Punctuation (1 sample each)

```
. , ! ? : ; ' " - _ ( ) / & @
```

15 characters × 1 sample = **15 glyphs**

### Space

Spacing is inferred from the inter-glyph spacing observed in the worksheet cells rather than captured as an explicit glyph. A calibration row of three space-separated words is printed at the bottom of the last worksheet page for this purpose.

### Totals

| Category | Characters | Samples Each | Glyphs |
|---|---|---|---|
| Lowercase | 26 | 3 | 78 |
| Uppercase | 26 | 2 | 52 |
| Digits | 10 | 2 | 20 |
| Punctuation | 15 | 1 | 15 |
| **Total** | **77** | — | **165** |

---

## 5. Worksheet Specification

The worksheet is the most critical component of the pipeline. Its design determines the accuracy and robustness of automated glyph extraction.

### 5.1 Page Layout

| Property | Value |
|---|---|
| Paper size | A4 (210 × 297mm) or US Letter (215.9 × 279.4mm) — auto-detected via QR metadata |
| Orientation | Landscape — provides more columns and reduces the number of pages |
| Margins | 12mm on all sides |
| Background | White |
| Print color | Black at 600 DPI minimum recommended |

### 5.2 Grid Structure

The worksheet is organized as a labeled grid of character cells.

- **Column headers:** character name (e.g., `a`, `B`, `3`, `.`) printed above each column
- **Row headers:** variant number (`v1`, `v2`, `v3`) printed to the left of each row
- **Cell padding:** 2mm internal padding within each cell box
- **Cell label:** small light-gray text (`a·1`, `a·2`, `a·3`) in the top-left corner of each cell, printed at 6pt to serve as ground truth labeling without obscuring the writing area

Example grid header structure:

```
       a      b      c      d      e      f   ...
  v1 [    ] [    ] [    ] [    ] [    ] [    ] ...
  v2 [    ] [    ] [    ] [    ] [    ] [    ] ...
  v3 [    ] [    ] [    ] [    ] [    ] [    ] ...
```

### 5.3 Cell Format

Each cell is a **40 × 40mm** box.

Internal guidelines (printed in light gray, approximately 10% opacity):

| Line | Position from top | Purpose |
|---|---|---|
| Ascender line | 5mm | Upper bound for tall letters (h, l, d) |
| Cap height line | 8mm | Upper bound for capital letters |
| x-height line | 18mm | Top of lowercase body (x, a, e) |
| Baseline | 26mm | Writing baseline — the main reference line |
| Descender line | 33mm | Lower bound for descending letters (p, g, y) |

The baseline is printed slightly darker than the other guide lines to serve as the primary alignment reference.

### 5.4 Alignment Markers

Four **filled 8 × 8mm squares** are placed at the corners of the printable area (inside the margin boundary). These are used for:

1. **Perspective correction:** computing the homographic transform to flatten a photographed (non-scanned) worksheet
2. **Scale normalization:** deriving the pixel-to-millimeter ratio for the current scan
3. **Page identification:** verifying that the correct page of the worksheet has been uploaded

The markers are positioned at fixed offsets from the page corners:

- Top-left: 12mm from left, 12mm from top
- Top-right: 12mm from right, 12mm from top
- Bottom-left: 12mm from left, 12mm from bottom
- Bottom-right: 12mm from right, 12mm from bottom

### 5.5 ArUco Detection Markers

In addition to the filled-square alignment markers, each corner also contains an **ArUco marker** (4×4 dictionary, marker IDs 0–3) embedded at 15 × 15mm. These provide:

- Unambiguous corner identification (no rotation ambiguity)
- Page number encoding (bits 4–7 of each marker ID encode page index 1–3)
- Robust detection under partial occlusion, blur, or shadow

The ArUco markers are rendered inside the filled-square markers, with the black border of the ArUco serving as the outer edge of the alignment square.

### 5.6 QR Metadata Block

A **20 × 20mm QR code** is printed in the bottom-right margin of each page. It encodes a JSON payload:

```json
{
  "v": 1,
  "page": 1,
  "paper": "A4",
  "orientation": "landscape",
  "cols": 13,
  "rows": 3,
  "cell_mm": 40,
  "charset_version": "1.0.0",
  "generated": "2026-03-13"
}
```

The engine reads this QR code before processing to validate that the uploaded image matches an expected worksheet configuration and to skip manual dimension inference.

### 5.7 Page Sequence

The 165 glyph slots are distributed across three worksheet pages to keep each page manageable (approximately 55 cells per page).

| Page | Contents |
|---|---|
| Page 1 | Lowercase `a`–`z`, all 3 variants (78 cells, 13 columns × 6 rows) |
| Page 2 | Lowercase variants 2–3 overflow + Uppercase `A`–`M` (2 variants each, 52 cells) |
| Page 3 | Uppercase `N`–`Z` + Digits `0`–`9` + Punctuation + space calibration row |

All three pages must be submitted together for a complete font. The engine accepts partial submissions and marks missing glyphs as absent rather than failing.

---

## 6. Glyph Extraction Pipeline

The extraction pipeline converts a raw worksheet image into a set of cleaned, normalized glyph images ready for vectorization.

### Step 1: Worksheet Detection

**Input:** raw JPEG, PNG, HEIC, or TIFF image (up to 10MB)

**Process:**
1. Decode image and convert to grayscale
2. Locate ArUco markers using OpenCV `aruco.detectMarkers()` with the 4×4 dictionary
3. Fall back to filled-square corner detection (adaptive threshold + contour area filter) if ArUco detection fails
4. Compute homographic transform from the four detected corner points to a canonical flat-page coordinate system
5. Apply `cv2.warpPerspective()` to produce a rectified, top-down view of the worksheet
6. Read QR code from the bottom-right region using `pyzbar` to obtain grid metadata

**Output:** rectified worksheet image, grid metadata dict

**Failure modes:**
- Fewer than 3 corners detected → reject with error `WORKSHEET_NOT_DETECTED`
- QR code unreadable → attempt metadata inference from detected grid dimensions; warn user
- Page number mismatch → reject with error `WRONG_PAGE`

### Step 2: Cell Segmentation

**Input:** rectified worksheet image, grid metadata

**Process:**
1. Compute expected cell bounding boxes from grid metadata (columns, rows, cell size in mm, resolved to pixels via the corner marker scale)
2. Extract each cell as a sub-image with 2mm inset from the cell border (to exclude the printed box border)
3. Validate each extracted cell: check that the cell is not blank (ink coverage > 0.5%) and not over-filled (ink coverage < 80%)
4. Tag each cell with its character identity and variant index derived from its grid position and the QR page metadata

**Output:** list of `(character, variant_index, cell_image)` tuples

### Step 3: Image Cleanup

**Input:** individual cell image (grayscale)

**Process:**
1. Apply Otsu's thresholding to produce a binary image
2. Remove the printed cell label (top-left 8 × 5mm region) by zeroing that area
3. Remove the printed guidelines by subtracting a template of the expected guideline positions (generated from QR metadata) before thresholding
4. Apply morphological opening with a 1px kernel to remove noise
5. Find the bounding box of remaining ink pixels and crop with a 2px margin

**Output:** cleaned binary glyph image, tight-cropped

### Step 4: Baseline Normalization

**Input:** cleaned binary glyph image, known baseline pixel position (from QR metadata + scale)

**Process:**
1. Locate the baseline in the cell coordinate system
2. Compute vertical shift to align the glyph's ink center-of-mass to the expected baseline offset for its character category (ascender, cap height, x-height, baseline, descender)
3. Scale the glyph to a canonical 200 × 200px bounding box while preserving aspect ratio and the baseline position
4. Pad to exactly 200 × 200px

**Output:** 200 × 200px normalized binary glyph image with consistent baseline positioning

### Step 5: Vectorization

**Input:** normalized binary glyph image

**Process:**
1. Use `potrace` (via `pypotrace` Python bindings) to trace the binary bitmap into smooth Bezier curves
2. Output SVG path data for each glyph
3. Simplify path with a tolerance of 0.5px to reduce node count without visible quality loss
4. Store as a list of SVG `<path>` elements in the glyph database

**Output:** SVG path string per glyph variant

---

## 7. Glyph Variant System

Multiple samples of the same character produce multiple glyph variants. During text rendering, the engine selects among available variants to avoid the mechanical repetition that makes digital text obviously non-handwritten.

### Variant Storage

```python
# Glyph database schema (SQLite)
CREATE TABLE glyphs (
    id          INTEGER PRIMARY KEY,
    character   TEXT NOT NULL,      -- e.g., 'a', 'B', '3', '.'
    variant     INTEGER NOT NULL,   -- 1-indexed
    svg_path    TEXT NOT NULL,      -- SVG path data
    bbox_width  REAL NOT NULL,      -- advance width in canonical units
    baseline_y  REAL NOT NULL,      -- baseline y in canonical units
    created_at  TEXT NOT NULL
);
```

### Variant Selection Strategy

During rendering, variants are selected using a **weighted random shuffle** that avoids immediately repeating the same variant:

1. When the same character appears consecutively, the previously used variant is down-weighted by 0.1 for the next two positions.
2. Selection is drawn from the weighted distribution using `random.choices()`.
3. The variant history is maintained per rendering session and reset between output documents.

---

## 8. Handwriting Renderer

The renderer assembles individual glyphs into lines and pages of text that approximate the appearance of genuine handwriting.

### 8.1 Glyph Placement

Glyphs are placed sequentially along a baseline. Each glyph's advance width is the `bbox_width` stored in the database, scaled by the requested font size.

### 8.2 Baseline Jitter

A small vertical offset is applied to each glyph to simulate the natural inconsistency in handwriting:

- Per-glyph offset: sampled from a zero-mean Gaussian with σ = 1.5px at 72 DPI (scales with output DPI)
- The jitter is correlated across adjacent glyphs using an exponential moving average with α = 0.4, so motion is smooth rather than noisy

### 8.3 Spacing Variation

Inter-glyph spacing is varied per character pair:

- Base spacing: derived from the stored advance widths
- Per-pair variation: ±15% of the base spacing, sampled uniformly
- Word spacing: base space width × 1.0, with ±10% variation per word

### 8.4 Rotation Variation

Each glyph is rotated by a small angle around its baseline attachment point:

- Rotation: sampled from a zero-mean Gaussian with σ = 0.8°
- Clamped to ±2.5° to prevent extreme slant on individual characters

### 8.5 Line Drift

The baseline itself drifts across a line to simulate the way handwriting rarely stays perfectly horizontal:

- Drift model: a low-frequency sine wave with random phase and amplitude 0–3px per line, plus a slow linear drift of 0–1px across the full line width
- Parameters are resampled per line

### 8.6 Rendering Stack

The renderer produces output as a composited image:

1. For each character in the input text, select variant and compute position
2. Apply rotation, jitter, and spacing offsets
3. Rasterize the SVG glyph path at the target DPI using `cairosvg` or `Pillow` + `aggdraw`
4. Composite onto the page canvas with alpha blending
5. Optionally apply a subtle paper texture overlay (bundled PNG, user can supply custom)

---

## 9. Font Generation

Font generation is an optional export that wraps the extracted glyphs in a standard TrueType font file.

### 9.1 Toolchain

- **`fonttools`** (Python): assembles TTF tables
- **`ufo2ft`**: converts UFO font sources to binary TTF/OTF
- The glyph SVG paths are first converted to UFO glyph format, then compiled

### 9.2 Font Tables

The generated font includes the following OpenType tables:

| Table | Contents |
|---|---|
| `head` | Font revision, bounding box, flags |
| `hhea` | Ascender, descender, line gap |
| `OS/2` | Weight class (400 Regular), panose values |
| `cmap` | Unicode BMP mapping for all captured characters |
| `glyf` | Glyph outlines (TrueType quadratic Beziers, converted from cubic) |
| `hmtx` | Advance widths and left side bearings |
| `kern` | Basic kerning pairs derived from the advance width measurements |
| `GSUB` | OpenType `aalt` (All Alternates) feature listing all glyph variants |

### 9.3 Glyph Alternates

All variants beyond the first are stored as named alternates (`a.alt1`, `a.alt2`, etc.) and exposed via the OpenType `aalt` feature. Applications that support OpenType alternates (Adobe InDesign, Affinity Publisher) can cycle through variants. Applications that do not support alternates will use the primary glyph.

### 9.4 Metrics

Font metrics are computed from the worksheet's known cell dimensions and guideline positions:

```
Units per em:    1000
Ascender:        750   (ascender line to baseline ratio)
Cap height:      680
x-height:        480
Descender:      -200   (descender line below baseline)
Line gap:        0
```

---

## 10. Note and Card Generator

The note generator takes text input and renders it as a handwritten-style image using the extracted glyph set.

### 10.1 Page Presets

| Preset | Dimensions | Line spacing | Margins |
|---|---|---|---|
| `note` | 148 × 210mm (A5) | 8mm | 15mm |
| `letter` | 210 × 297mm (A4) | 10mm | 20mm |
| `card` | 105 × 148mm (A6) | 7mm | 10mm |
| `postcard` | 148 × 105mm (landscape A6) | 7mm | 10mm |

### 10.2 Background Options

- Plain white
- Ruled lines (line spacing matches the preset's line spacing value)
- Grid (5mm squares)
- Blank aged paper (bundled texture PNG)

### 10.3 Text Layout

- Text is wrapped at word boundaries to fit within the margin-adjusted page width
- Automatic hyphenation is not applied in v1
- Overflow onto additional pages is supported; multi-page output is packaged as a multi-page PDF

### 10.4 Export Formats

| Format | Description |
|---|---|
| PNG | Single image per page at 150 DPI (screen) or 300 DPI (print) |
| SVG | Vector output per page; glyph paths embedded directly |
| PDF | Multi-page PDF via `reportlab` or `fpdf2`; 300 DPI rasterized glyphs embedded |

---

## 11. API Endpoints

The backend exposes a REST API. All endpoints use JSON request/response bodies except where noted (file uploads use `multipart/form-data`).

### Worksheet

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/worksheet/generate` | Generate and return a worksheet PDF |
| `POST` | `/api/worksheet/upload` | Upload a completed worksheet image for processing |
| `GET` | `/api/worksheet/status/{job_id}` | Poll extraction job status |

**`GET /api/worksheet/generate`**

Query parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `paper` | `A4` \| `letter` | `A4` | Paper size |
| `page` | `1` \| `2` \| `3` \| `all` | `all` | Which pages to include |

Response: `application/pdf`

**`POST /api/worksheet/upload`**

Request: `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | binary | yes | Worksheet image (JPEG, PNG, HEIC, TIFF; max 10MB) |
| `page` | integer | yes | Page number (1, 2, or 3) |

Response:

```json
{
  "job_id": "string",
  "status": "queued",
  "estimated_seconds": 8
}
```

**`GET /api/worksheet/status/{job_id}`**

Response:

```json
{
  "job_id": "string",
  "status": "queued|processing|complete|failed",
  "progress": 0.72,
  "glyphs_extracted": 54,
  "glyphs_total": 78,
  "errors": [],
  "result_url": "/api/glyphs/export?job_id=..."
}
```

### Glyphs

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/glyphs` | List all extracted glyphs for the current session |
| `GET` | `/api/glyphs/{character}` | Get all variants for a specific character |
| `DELETE` | `/api/glyphs/{character}/{variant}` | Delete a specific glyph variant |
| `POST` | `/api/glyphs/{character}/{variant}/replace` | Replace a glyph with a re-uploaded cell image |

**`GET /api/glyphs`**

Response:

```json
{
  "total": 165,
  "captured": 148,
  "missing": ["q", "Q", "X"],
  "glyphs": [
    {
      "character": "a",
      "variants": [
        { "variant": 1, "svg_preview": "data:image/svg+xml;base64,...", "quality_score": 0.91 }
      ]
    }
  ]
}
```

### Font

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/font/generate` | Generate a TTF font from extracted glyphs |
| `GET` | `/api/font/download/{font_id}` | Download a generated font file |

**`POST /api/font/generate`**

Request:

```json
{
  "font_name": "string",
  "include_alternates": true
}
```

Response:

```json
{
  "font_id": "string",
  "status": "generating",
  "estimated_seconds": 4
}
```

### Notes

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/notes/render` | Render text as a handwritten note |
| `GET` | `/api/notes/download/{note_id}` | Download a rendered note |

**`POST /api/notes/render`**

Request:

```json
{
  "text": "string",
  "preset": "note|letter|card|postcard",
  "background": "plain|ruled|grid|aged",
  "font_size_pt": 14,
  "export_format": "png|svg|pdf",
  "dpi": 300
}
```

Response:

```json
{
  "note_id": "string",
  "pages": 2,
  "download_url": "/api/notes/download/..."
}
```

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Service health check |

**`GET /api/health`**

Response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "opencv_available": true,
  "potrace_available": true,
  "fonttools_available": true
}
```

---

## 12. Architecture

### 12.1 Component Overview

```
┌─────────────────────────────────────┐
│           Browser (user)            │
└──────────────┬──────────────────────┘
               │ HTTP
┌──────────────▼──────────────────────┐
│         Web Frontend                │
│  Next.js 14 + TypeScript + Tailwind │
│  - Worksheet download UI            │
│  - Upload + progress polling        │
│  - Glyph review and replacement     │
│  - Note composer                    │
│  - Font download                    │
└──────────────┬──────────────────────┘
               │ HTTP (REST)
┌──────────────▼──────────────────────┐
│         Backend API                 │
│  Python 3.12 + FastAPI              │
│  - Request validation               │
│  - Job queue (asyncio + background) │
│  - Session state (SQLite)           │
│  - File handling                    │
└──────────────┬──────────────────────┘
               │ Python calls
┌──────────────▼──────────────────────┐
│         Processing Engine           │
│  OpenCV — detection, segmentation   │
│  Pillow — cleanup, normalization    │
│  pypotrace / potrace — vectorization│
│  fonttools + ufo2ft — font assembly │
│  cairosvg — SVG rasterization       │
│  pyzbar — QR code reading           │
└─────────────────────────────────────┘
```

### 12.2 Frontend

| Concern | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS 3 |
| State | React `useState` / `useReducer` (no external state library for v1) |
| API client | Native `fetch` with typed response wrappers |
| File upload | Browser `FormData` with `XMLHttpRequest` progress events |
| PDF preview | `react-pdf` (Mozilla PDF.js wrapper) |

The frontend communicates exclusively with the backend REST API. There is no direct browser-to-engine communication.

### 12.3 Backend

| Concern | Technology |
|---|---|
| Framework | FastAPI 0.115+ |
| Language | Python 3.12 |
| Server | Uvicorn with a single worker (concurrency via asyncio) |
| Database | SQLite (via `aiosqlite`) — stores glyph data and job state |
| Job queue | In-process asyncio background tasks (no external broker for v1) |
| Session model | Session ID generated per browser session, stored in a cookie; no authentication |
| File storage | Local filesystem, temp directory per session, cleaned on session expiry |

### 12.4 Engine

The engine is a Python package (`handwright.engine`) imported directly by the backend. It is not a separate service. This simplifies deployment and avoids inter-process communication overhead.

| Module | Responsibility |
|---|---|
| `engine.detection` | ArUco/corner detection, perspective correction, QR reading |
| `engine.segmentation` | Cell extraction, blank/overflow validation |
| `engine.cleanup` | Thresholding, guideline removal, noise reduction |
| `engine.normalization` | Baseline alignment, canonical sizing |
| `engine.vectorization` | potrace integration, SVG path output |
| `engine.renderer` | Glyph placement, jitter, spacing, line layout, rasterization |
| `engine.font` | UFO assembly, fonttools compilation, TTF output |

### 12.5 Deployment

The production deployment is a Docker Compose stack with two services:

```yaml
services:
  web:
    build: ./web
    ports:
      - "3000:3000"

  api:
    build: ./engine
    ports:
      - "8000:8000"
    volumes:
      - handwright_data:/data
```

The frontend at `localhost:3000` proxies API calls to `localhost:8000`. No reverse proxy is required for local deployment; an optional Caddy configuration is documented for public self-hosting.

---

## 13. Security

### 13.1 Input Validation

- **File size limit:** 10MB maximum per upload, enforced at the FastAPI middleware level before the file reaches disk
- **Format whitelist:** only JPEG, PNG, HEIC, and TIFF are accepted; validated by magic bytes, not file extension
- **Image dimensions:** maximum 8000 × 8000px; larger images are rejected with a `413` response
- **Text input:** maximum 50,000 characters for note rendering; no HTML allowed; input is treated as plain text and never interpreted

### 13.2 File Handling

- Uploaded files are written to a per-session temporary directory under `/tmp/handwright/<session_id>/`
- Temporary files are deleted immediately after processing completes or within 1 hour of session inactivity, whichever comes first
- The application never reads files outside its designated data directory

### 13.3 Process Isolation

- The `potrace` binary is invoked via `subprocess` with a strict argument allowlist; no shell interpolation is used
- External binary calls use `subprocess.run()` with `shell=False` and explicit argument lists
- Timeouts are enforced on all external process calls (default: 30 seconds)

### 13.4 Signature Cloning and Ethics

Handwright explicitly refuses to:

- Accept input framed as a signature or legal mark
- Export glyphs in a format marketed for signature reproduction
- Provide any API endpoint that combines name + signature-style glyph sets

The `POST /api/notes/render` endpoint includes a content-type flag. If the frontend detects that the text input matches common signature patterns (name alone, name + date), it presents an educational notice that the output is not suitable for legal documents.

This is an ethical design decision, not a security control. It does not prevent misuse but makes the project's intent explicit.

### 13.5 No External Communication

The application makes no outbound network requests at runtime. All dependencies are bundled in the Docker image. There is no telemetry, no update check, no license validation.

---

## 14. Performance Targets

| Operation | Target | Measurement Condition |
|---|---|---|
| Worksheet PDF generation | < 1 second | All 3 pages |
| Worksheet detection (ArUco + QR) | < 2 seconds | 10MP JPEG, cold start |
| Full worksheet processing (1 page, 78 cells) | < 10 seconds | 10MP JPEG, single-core |
| Font generation | < 5 seconds | 165 glyphs, all variants |
| Note rendering (1 page, 300 DPI PNG) | < 1 second | After glyph DB loaded |
| API response (health check) | < 50ms | Local deployment |

These targets are measured on a commodity x86-64 machine (4-core, 8GB RAM) running the Docker Compose stack. They are not guarantees but inform optimization priorities.

---

## 15. Success Criteria

The project is considered feature-complete for v1 when:

1. A user with no technical background can produce a usable custom font in under 10 minutes of active effort (print, write, scan, upload, download TTF)
2. Rendered text using the generated font is judged as handwritten by at least 8 out of 10 casual observers in informal testing
3. The full application runs locally with a single `docker compose up` command on Linux, macOS, and Windows (WSL2)
4. No user data leaves the local machine during any part of the workflow
5. The self-hosting setup requires no external accounts, API keys, or paid services
6. All three export formats (PNG, SVG, PDF) produce correctly rendered output

---

## 16. Development Milestones

| Milestone | Scope | Deliverable |
|---|---|---|
| **M1: Worksheet** | Design and render the 3-page worksheet PDF with ArUco markers, QR codes, and cell guidelines | Printable PDF, `GET /api/worksheet/generate` endpoint |
| **M2: Detection** | Implement worksheet detection pipeline: ArUco corner finding, perspective correction, QR reading, cell segmentation | `engine.detection` and `engine.segmentation` modules, unit tests with sample scans |
| **M3: Extraction** | Implement glyph cleanup, baseline normalization, and potrace vectorization | `engine.cleanup`, `engine.normalization`, `engine.vectorization` modules; glyph review UI |
| **M4: Renderer** | Implement handwriting renderer with variant selection, jitter, and spacing variation; note/card generator with PDF export | `engine.renderer` module; `POST /api/notes/render` endpoint; frontend note composer |
| **M5: Font Export** | Implement TTF font generation with OpenType alternates via fonttools | `engine.font` module; `POST /api/font/generate` endpoint; font download UI |
| **M6: Polish and Packaging** | Docker Compose stack, Caddy self-hosting docs, end-to-end testing, performance validation, README | Docker images, deployment documentation, passing E2E test suite |
