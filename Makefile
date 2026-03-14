.PHONY: dev dev-frontend dev-api build test lint docker-up docker-down clean release changelog

# Start both frontend and backend in development mode (parallel)
dev:
	@echo "Starting frontend and API in development mode..."
	@$(MAKE) -j2 dev-frontend dev-api

# Start only the Next.js frontend
dev-frontend:
	cd web/frontend && pnpm dev

# Start only the FastAPI backend
dev-api:
	cd web/api && uvicorn main:app --reload --port 8000

# Build all packages for production
build:
	@echo "Building frontend..."
	cd web/frontend && pnpm build
	@echo "Build complete."

# Run all tests (frontend + backend)
test:
	@echo "Running frontend tests..."
	cd web/frontend && pnpm test --passWithNoTests
	@echo "Running backend tests..."
	cd web/api && python -m pytest tests/ -v
	@echo "Running engine tests..."
	python -m pytest engine/tests/ -v

# Lint all code (TypeScript + Python)
lint:
	@echo "Linting frontend..."
	cd web/frontend && pnpm lint
	@echo "Linting backend and engine with ruff..."
	ruff check web/api/ engine/

# Start services with Docker Compose
docker-up:
	docker compose up --build

# Stop Docker Compose services
docker-down:
	docker compose down

# Remove build artifacts, caches, and generated files
clean:
	@echo "Cleaning frontend build artifacts..."
	rm -rf web/frontend/.next web/frontend/dist web/frontend/node_modules
	@echo "Cleaning Python caches..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

# Bump version, commit, and tag for release
# Usage: make release VERSION=0.3.0
release:
ifndef VERSION
	$(error VERSION is required. Usage: make release VERSION=0.3.0)
endif
	@echo "Releasing v$(VERSION)..."
	sed -i 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml
	git add pyproject.toml
	git commit -m "chore: release v$(VERSION)"
	git tag v$(VERSION)
	@echo ""
	@echo "Release v$(VERSION) committed and tagged locally."
	@echo "To publish, run:"
	@echo "  git push && git push origin v$(VERSION)"

# Show commits since the last tag
changelog:
	git log $(shell git describe --tags --abbrev=0 2>/dev/null || echo HEAD)..HEAD --oneline --no-decorate
