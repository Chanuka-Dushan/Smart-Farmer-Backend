#!/bin/sh
set -e

echo "Starting Smart Farmer Backend..."
echo "Current working directory: $(pwd)"
echo "Listing files in current directory:"
ls -la

echo "Python version:"
python --version

echo "Installed packages:"
pip list | grep -E "gunicorn|uvicorn|fastapi"

echo "Starting Gunicorn..."
exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8080 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
