# Handwright - Claude Code Instructions

**Project:** Handwriting font generator and note renderer
**Repository:** handwright (local monorepo)

---

## Quick Commands

```bash
make dev           # Start frontend + API in parallel (development)
make dev-frontend  # Next.js only (port 3000)
make dev-api       # FastAPI only (port 8000)
make test          # Run all tests (frontend + backend + engine)
make lint          # Lint TypeScript (ESLint) + Python (ruff)
make build         # Production build (frontend)
make docker-up     # Start all services via Docker Compose
make docker-down   # Stop Docker Compose services
make clean         # Remove build artifacts and caches
```

---

## Repository Layout

```
handwright/
├── engine/               # Python processing library (installable package)
│   ├── worksheet/        # Worksheet PDF generation
│   ├── segmentation/     # Glyph detection and extraction (OpenCV)
│   ├── glyphs/           # Glyph normalization and storage
│   ├── fontgen/          # .ttf font generation (fonttools + potrace)
│   └── renderer/         # Handwritten message rendering
├── web/
│   ├── frontend/         # Next.js 15 app (TypeScript + Tailwind)
│   └── api/              # FastAPI server (Python 3.11)
├── docker-compose.yml
├── Makefile
└── CLAUDE.md             # This file
```

---

## Stack

| Layer      | Technology                                      |
| ---------- | ----------------------------------------------- |
| Frontend   | Next.js 15, TypeScript (strict), Tailwind CSS   |
| Backend    | Python 3.11, FastAPI, uvicorn                   |
| Engine     | OpenCV, Pillow, fonttools, potrace, numpy        |
| Deployment | Docker Compose                                  |

---

## Conventions

### TypeScript (Frontend)
- `strict: true` in tsconfig — no implicit `any`
- ESLint enforced via `eslint.config.mjs`
- Components in `src/components/`, pages in `src/app/` (App Router)
- API calls go through `src/lib/api.ts`

### Python (Backend + Engine)
- Type hints on all functions — no bare `Any` without a comment explaining why
- `ruff` for linting and formatting (`ruff check`, `ruff format`)
- `pytest` for tests; test files live in `tests/` within each package
- FastAPI route handlers in `web/api/routes/`; business logic stays in `engine/`

### API Contract
- REST API at `http://localhost:8000`
- Health check: `GET /health`
- OpenAPI docs: `http://localhost:8000/docs`

---

## Core Principles

- **Local-first**: all processing happens on the user's machine — no data leaves
- **Correctness over cleverness**: glyph extraction must be deterministic and testable
- **No silent failures**: every image processing step must surface errors to the user
