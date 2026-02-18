# =============================================================================
# Multi-stage Dockerfile for LLM Ranking Service
# Author: Gopi Krishna Vajrala
# Optimized for production: small image, non-root user, health checks
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install \
    fastapi==0.115.6 \
    uvicorn[standard]==0.34.0 \
    gunicorn==23.0.0 \
    pydantic==2.10.4 \
    pydantic-settings==2.7.1 \
    numpy==2.2.1 \
    python-jose[cryptography]==3.3.0 \
    prometheus-client==0.21.1 \
    prometheus-fastapi-instrumentator==7.0.2 \
    structlog==24.4.0 \
    slowapi==0.1.9 \
    orjson==3.10.13 \
    python-dotenv==1.0.1 \
    tenacity==9.0.0 \
    python-multipart==0.0.20

# Stage 2: Production image
FROM python:3.11-slim as production

# Security: run as non-root
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY .env.example .env

# Create model cache directory
RUN mkdir -p /app/models && chown -R appuser:appuser /app

USER appuser

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    MODEL_DEVICE=cpu

EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run with gunicorn + uvicorn workers for production
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
