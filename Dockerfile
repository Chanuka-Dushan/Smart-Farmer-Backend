# Production Dockerfile for DigitalOcean
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and constraints
COPY backend/requirements.txt .
COPY backend/constraints.txt .

# Install Python dependencies - use constraints to BLOCK opencv-python at pip level
# This prevents ultralytics from installing opencv-python (GUI version)
# Use pip cache to speed up DigitalOcean rebuilds (cache persists between builds)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    echo "📦 Installing opencv-python-headless..." && \
    pip install opencv-python-headless>=4.8.0 && \
    echo "📦 Installing requirements with constraints..." && \
    PIP_CONSTRAINT=constraints.txt pip install -r requirements.txt && \
    echo "✅ OpenCV check:" && \
    pip list | grep opencv

# Copy application code
COPY backend/ /app/

# Copy and make entrypoint script executable
COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
