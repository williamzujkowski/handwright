# Handwright

Turn your handwriting into a custom font and realistic handwritten messages.

## Features
- Generate printable worksheets for handwriting capture
- Extract glyphs from photos/scans automatically
- Generate custom .ttf handwriting fonts
- Render realistic handwritten notes, cards, and letters
- Local-first, self-hostable, privacy-preserving

## Quick Start

```bash
docker compose up
# Open http://localhost:3000
```

## Development

### Prerequisites
- Node.js 22+ and pnpm
- Python 3.11+
- Docker (optional, for containerized deployment)

### Setup
```bash
# Frontend
cd web/frontend && pnpm install && pnpm dev

# Backend
cd web/api && pip install -e "../../[dev]" && uvicorn main:app --reload --port 8000
```

## Architecture
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **Backend**: Python + FastAPI
- **Engine**: OpenCV + Pillow + fonttools + potrace
- **Deployment**: Docker Compose

## How It Works
1. **Write** — Fill in the generated worksheet with your handwriting
2. **Upload** — Take a photo or scan the worksheet
3. **Extract** — System detects and extracts individual character glyphs
4. **Generate** — Create a custom font or render handwritten messages

## License
MIT
