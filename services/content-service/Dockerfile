FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SERVICE_NAME=content-service \
    SERVICE_VERSION=1.0.0 \
    SERVICE_PORT=8002

# Create app directory
WORKDIR /app

# Install system dependencies for content processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libmagic1 \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-fra \
        tesseract-ocr-deu \
        tesseract-ocr-spa \
        imagemagick \
        poppler-utils \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd -r contentuser \
    && useradd -r -g contentuser -d /app -s /bin/bash contentuser \
    && chown -R contentuser:contentuser /app

# Create directories with proper permissions
RUN mkdir -p /app/{uploads,storage,logs} \
    && chown -R contentuser:contentuser /app

# Copy application code
COPY --chown=contentuser:contentuser . .

# Switch to non-root user
USER contentuser

# Expose service port
EXPOSE 8002

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]