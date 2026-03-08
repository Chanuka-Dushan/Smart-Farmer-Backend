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

# Install Python dependencies - ABSOLUTE BLOCK of opencv-python (GUI)
# Create pip.conf to globally block opencv-python installations
RUN mkdir -p /root/.config/pip && \
    echo "[install]" > /root/.config/pip/pip.conf && \
    echo "no-binary = opencv-python,opencv-contrib-python" >> /root/.config/pip/pip.conf

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    echo "📦 Step 1: Install opencv-python-headless FIRST (lock it)..." && \
    pip install opencv-python-headless==4.10.0.84 && \
    \
    echo "📦 Step 2: Install ultralytics WITHOUT any deps..." && \
    pip install --no-deps ultralytics==8.2.103 && \
    \
    echo "📦 Step 3: Install ultralytics dependencies manually..." && \
    pip install matplotlib==3.8.2 pillow==10.1.0 pyyaml requests tqdm && \
    pip install pandas seaborn psutil py-cpuinfo thop scipy && \
    \
    echo "📦 Step 4: Install OTHER requirements EXCEPT opencv and ultralytics..." && \
    grep -v "^opencv-python" requirements.txt | grep -v "^ultralytics" | grep -v "^#" | grep -v "^$" > /tmp/filtered_requirements.txt && \
    pip install -r /tmp/filtered_requirements.txt && \
    \
    echo "📦 Step 5: NUCLEAR CLEANUP - remove any opencv-python..." && \
    pip uninstall -y opencv-python opencv-contrib-python opencv-python-rolling 2>/dev/null || true && \
    \
    echo "📦 Step 6: Final reinstall of headless (safety)..." && \
    pip install --force-reinstall --no-deps opencv-python-headless==4.10.0.84 && \
    \
    echo "📦 Step 7: VERIFICATION (will fail build if GUI opencv found)..." && \
    pip list | grep opencv && \
    if pip list | grep -E "^opencv-python " | grep -v "headless"; then \
        echo "❌ FATAL: opencv-python GUI version detected!"; \
        exit 1; \
    fi && \
    echo "✅ SUCCESS: Only opencv-python-headless is installed"

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
