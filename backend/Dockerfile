# Multi-stage production Dockerfile for Agent WAF FastAPI Backend Service
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency manifests and build virtual environment
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Stage 2: Final lightweight production runner
FROM python:3.12-slim as runner

WORKDIR /app

# Create non-root app user for container security hardening
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser

# Install runtime PostgreSQL client library & curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv and application codebase from builder
COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appgroup . /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production \
    WAF_MODE=ENFORCE

USER appuser

EXPOSE 8000

# Container Healthcheck probe matching FastAPI root health route (/health)
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production Uvicorn Server execution
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
