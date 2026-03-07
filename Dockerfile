# Production Dockerfile for DigitalOcean
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Install system dependencies
# Note: libgl1-mesa-glx is NOT installed - we use headless opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and constraints
COPY backend/requirements.txt .
COPY backend/constraints.txt .

# Install Python dependencies - FAST BUILD with opencv-python blocking
# Strategy: Use pip cache + install opencv-headless first + block GUI opencv
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    echo "📦 Installing opencv-python-headless FIRST..." && \
    pip install opencv-python-headless==4.10.0.84 && \
    echo "📦 Installing ultralytics WITHOUT dependencies..." && \
    pip install --no-deps ultralytics==8.2.103 && \
    echo "📦 Installing ultralytics dependencies (cached)..." && \
    pip install matplotlib==3.8.2 pillow==10.1.0 pyyaml requests tqdm pandas seaborn psutil py-cpuinfo thop scipy && \
    echo "📦 Installing remaining requirements (cached)..." && \
    pip install -r requirements.txt && \
    echo "🔍 Checking for opencv-python (GUI)..." && \
    pip uninstall -y opencv-python opencv-contrib-python opencv-python-rolling 2>/dev/null || true && \
    pip install --force-reinstall --no-deps opencv-python-headless==4.10.0.84 && \
    if pip list | grep -E "^opencv-python " | grep -v headless; then \
        echo "❌ FATAL: opencv-python (GUI) detected!"; exit 1; \
    fi && \
    echo "✅ Build complete - only opencv-python-headless:" && pip list | grep opencv

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
