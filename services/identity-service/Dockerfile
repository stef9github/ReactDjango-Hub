# Multi-stage build for Auth Service
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-standalone.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r identityuser \
    && useradd -r -g identityuser -d /app -s /bin/bash identityuser \
    && chown -R identityuser:identityuser /app

# Copy Python dependencies from builder with proper ownership
COPY --from=builder --chown=identityuser:identityuser /root/.local /home/identityuser/.local

# Copy application code with proper ownership
COPY --chown=identityuser:identityuser . .

# Switch to non-root user
USER identityuser

# Make sure the PATH includes user local installed packages
ENV PATH=/home/identityuser/.local/bin:$PATH

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/home/identityuser/.local/lib/python3.11/site-packages \
    SERVICE_PORT=8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]