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

# Install Python dependencies - FORCE opencv-python-headless only
# Strategy: Use constraints.txt to block GUI opencv, install headless first
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    echo "📦 Step 1: Install opencv-python-headless FIRST..." && \
    pip install --no-cache-dir opencv-python-headless>=4.8.0 && \
    echo "📦 Step 2: Install ALL requirements using constraints to block GUI opencv..." && \
    pip install --no-cache-dir -c constraints.txt -r requirements.txt && \
    echo "📦 Step 3: VERIFY and remove any opencv-python (GUI) if present..." && \
    pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true && \
    echo "📦 Step 4: Final safety check - reinstall headless..." && \
    pip install --no-cache-dir --force-reinstall --no-deps opencv-python-headless>=4.8.0 && \
    echo "✅ Final verification - should ONLY show opencv-python-headless:" && \
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
