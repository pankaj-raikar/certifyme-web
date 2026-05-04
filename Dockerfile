# CertifyMe Production Dockerfile
# Multi-stage build for optimized production image

# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
FROM python:3.12-slim AS builder

# Install uv package manager (fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies (production only, no dev dependencies)
RUN uv sync --frozen --no-dev --no-editable

# ============================================
# Stage 2: Production Runtime
# ============================================
FROM python:3.12-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r certifyme && useradd -r -g certifyme certifyme

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /app/.venv /app/.venv

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=certifyme:certifyme . .

# Create instance directory for SQLite database
RUN mkdir -p /app/instance && chown -R certifyme:certifyme /app/instance

# Create directory for static files serving
RUN mkdir -p /app/static && chown -R certifyme:certifyme /app/static

# Copy frontend files to static directory for production serving
RUN cp -r /app/sky/* /app/static/

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    # Default values (should be overridden at runtime)
    SECRET_KEY="" \
    DATABASE_URL="sqlite:///instance/app.db" \
    FRONTEND_ORIGIN="" \
    SESSION_LIFETIME_DAYS=30

# Switch to non-root user
USER certifyme

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/auth/me || exit 1

# Create entrypoint script for database migration
COPY --chown=certifyme:certifyme docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Entry point - runs migrations then starts server
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - gunicorn production server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "run:app"]