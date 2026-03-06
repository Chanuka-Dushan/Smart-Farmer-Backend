#!/bin/bash
# Script to fix OpenCV installation by removing GUI version and installing headless

echo "🔧 Fixing OpenCV installation..."

# Uninstall opencv-python if installed
pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true

# Install headless version
pip install opencv-python-headless>=4.8.0

echo "✅ OpenCV headless installed"
pip show opencv-python-headless
