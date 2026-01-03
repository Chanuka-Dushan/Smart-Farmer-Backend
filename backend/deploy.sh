#!/bin/bash

# Smart Farmer Backend - Production Deployment Script
# This script helps deploy the backend with optimized settings for production

echo "🚀 Smart Farmer Backend - Production Deployment"
echo "=============================================="

# Check if DISABLE_TENSORFLOW is set
if [ -z "$DISABLE_TENSORFLOW" ]; then
    echo "⚠️  TensorFlow not disabled. Setting DISABLE_TENSORFLOW=true for production..."
    export DISABLE_TENSORFLOW=true
fi

# Check if we're in production mode
if [ "$DISABLE_TENSORFLOW" = "true" ]; then
    echo "✅ TensorFlow disabled - using simulation mode for vision analysis"
    echo "💡 This improves startup time and prevents worker timeouts"
else
    echo "⚠️  TensorFlow enabled - this may cause slow startup in production"
fi

# Install dependencies (excluding TensorFlow if disabled)
echo "📦 Installing Python dependencies..."
if [ "$DISABLE_TENSORFLOW" = "true" ]; then
    # Install without TensorFlow
    pip install -r requirements.txt --no-deps
    echo "✅ Installed dependencies without TensorFlow"
else
    # Install everything including TensorFlow
    pip install -r requirements.txt
    echo "✅ Installed all dependencies including TensorFlow"
fi

# Run database migrations if needed
echo "🗄️  Setting up database..."
python -c "from main import Base, engine; Base.metadata.create_all(bind=engine)"
echo "✅ Database tables created/updated"

# Start the server
echo "🌐 Starting production server..."
if [ "$PORT" ]; then
    uvicorn main:app --host 0.0.0.0 --port $PORT
else
    uvicorn main:app --host 0.0.0.0 --port 8000
fi