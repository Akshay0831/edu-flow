# Multi-stage Docker build for Edu-Flow Backend API

# Stage 1: Base image with Python
FROM python:3.11-slim-bullseye as base

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements files
COPY requirements.txt .
COPY requirements-dev.txt .  # For development dependencies

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-dev.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Stage 3: Development with hot-reload
FROM dependencies as development

# Copy source code
COPY --chown=appuser:appuser . .

# Install development tools
RUN pip install --no-cache-dir pytest-watch pytest-cov black isort mypy

# Expose port
EXPOSE 8000

# Run development server
CMD ["uvicorn", "src.api.v1:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 4: Production build
FROM base as production

# Copy source code
COPY --chown=appuser:appuser . .

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/logs /app/reports

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Run the application
CMD ["uvicorn", "src.api.v1:app", "--host", "0.0.0.0", "--port", "8000"]