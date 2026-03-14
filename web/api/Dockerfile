# Python 3.12 slim base (LTS)
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files for installation
COPY pyproject.toml README.md ./
COPY engine/ ./engine/
COPY web/ ./web/

# Install the package with all dependencies
RUN pip install --no-cache-dir .

# Non-root user for security
RUN adduser --system --uid 1001 apiuser && \
    mkdir -p /app/uploads && \
    chown -R apiuser:nogroup /app

USER apiuser

EXPOSE 8000

CMD ["uvicorn", "web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
