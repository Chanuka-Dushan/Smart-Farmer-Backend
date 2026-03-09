#!/bin/bash
# OpenCV Cleanup Script for Headless Servers
# Removes opencv-python (GUI) and installs opencv-python-headless

set -e  # Exit on error

echo "============================================================"
echo "🔍 OpenCV Headless Installation Script"
echo "============================================================"

# Step 1: Show current OpenCV packages
echo ""
echo "📦 Step 1: Checking current OpenCV packages..."
pip list | grep opencv || echo "  No OpenCV packages found"

# Step 2: Uninstall ALL OpenCV variants
echo ""
echo "🗑️  Step 2: Removing all OpenCV packages..."
pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless opencv-contrib-python-headless 2>/dev/null || true

# Step 3: Clear pip cache
echo ""
echo "🧹 Step 3: Clearing pip cache..."
pip cache purge || true

# Step 4: Install system dependencies (if needed)
echo ""
echo "📦 Step 4: Checking system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "  Installing required system libraries..."
    apt-get update -qq
    apt-get install -y --no-install-recommends libglib2.0-0 || true
    echo "  ✅ System dependencies checked"
else
    echo "  ⚠️  apt-get not available, skipping system dependencies"
fi

# Step 5: Install opencv-python-headless
echo ""
echo "📥 Step 5: Installing opencv-python-headless..."
pip install --no-cache-dir opencv-python-headless==4.10.0.84

# Step 6: Verify installation
echo ""
echo "🔍 Step 6: Verifying installation..."
pip list | grep opencv

# Step 7: Test import
echo ""
echo "🧪 Step 7: Testing cv2 import..."
python3 << 'EOF'
import sys
try:
    import cv2
    print(f"✅ SUCCESS: cv2 imported successfully!")
    print(f"   Version: {cv2.__version__}")
    print(f"   Build: Headless")
    sys.exit(0)
except Exception as e:
    print(f"❌ FAILED: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✅ OpenCV headless installation successful!"
    echo "============================================================"
    exit 0
else
    echo ""
    echo "============================================================"
    echo "❌ OpenCV installation failed!"
    echo "============================================================"
    exit 1
fi
