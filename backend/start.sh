#!/bin/bash
# Startup script for Digital Ocean App Platform

# Set working directory
cd /workspace/backend 2>/dev/null || cd /app 2>/dev/null || true

# Print Python version and path for debugging
echo "Python version:"
python --version

echo "Current directory:"
pwd

echo "Directory contents:"
ls -la

echo "Python path:"
echo $PYTHONPATH

# Start the application
exec gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8080} --access-logfile - --error-logfile -
