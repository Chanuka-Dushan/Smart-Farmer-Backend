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

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies - force opencv-headless only
# Strategy: Install opencv-headless first, then uninstall GUI version after all deps
RUN pip install --upgrade pip && \
    echo "📦 Step 1: Installing opencv-python-headless..." && \
    pip install --no-cache-dir opencv-python-headless>=4.8.0 && \
    echo "📦 Step 2: Installing all requirements..." && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "🔍 Step 3: Checking for GUI opencv..." && \
    pip list | grep opencv && \
    echo "🧹 Step 4: Removing any GUI opencv..." && \
    pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true && \
    echo "🔍 Step 5: Verifying with conditional reinstall..." && \
    if pip list | grep -E "^opencv-python " | grep -v headless; then \
        echo "❌ ERROR: opencv-python (GUI) still detected! Force removing..." && \
        pip uninstall -y opencv-python opencv-contrib-python && \
        pip install --force-reinstall --no-cache-dir opencv-python-headless>=4.8.0; \
    fi && \
    echo "✅ Final OpenCV verification:" && \
    pip list | grep opencv && \
    echo "✅ Build complete"

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
