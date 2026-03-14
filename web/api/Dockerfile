# Python 3.11 slim base for a smaller image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required by OpenCV and other native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    potrace \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies before copying source
# so Docker can cache the layer when only source changes
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the engine package so the API can import it
COPY --from=. /engine /engine
RUN pip install --no-cache-dir -e /engine

# Copy API source
COPY . .

# Non-root user for security
RUN adduser --system --uid 1001 apiuser && \
    mkdir -p /app/uploads && \
    chown -R apiuser:apiuser /app

USER apiuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
