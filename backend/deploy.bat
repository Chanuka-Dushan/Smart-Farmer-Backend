@echo off
REM Smart Farmer Backend - Production Deployment Script (Windows)
REM This script helps deploy the backend with optimized settings for production

echo 🚀 Smart Farmer Backend - Production Deployment
echo ==============================================

REM Check if DISABLE_TENSORFLOW is set
if "%DISABLE_TENSORFLOW%"=="" (
    echo ⚠️  TensorFlow not disabled. Setting DISABLE_TENSORFLOW=true for production...
    set DISABLE_TENSORFLOW=true
)

REM Check if we're in production mode
if "%DISABLE_TENSORFLOW%"=="true" (
    echo ✅ TensorFlow disabled - using simulation mode for vision analysis
    echo 💡 This improves startup time and prevents worker timeouts
) else (
    echo ⚠️  TensorFlow enabled - this may cause slow startup in production
)

REM Install dependencies (excluding TensorFlow if disabled)
echo 📦 Installing Python dependencies...
if "%DISABLE_TENSORFLOW%"=="true" (
    REM Install without TensorFlow
    pip install -r requirements.txt --no-deps
    echo ✅ Installed dependencies without TensorFlow
) else (
    REM Install everything including TensorFlow
    pip install -r requirements.txt
    echo ✅ Installed all dependencies including TensorFlow
)

REM Run database migrations if needed
echo 🗄️  Setting up database...
python -c "from main import Base, engine; Base.metadata.create_all(bind=engine)"
echo ✅ Database tables created/updated

REM Start the server
echo 🌐 Starting production server...
if "%PORT%"=="" (
    uvicorn main:app --host 0.0.0.0 --port 8000
) else (
    uvicorn main:app --host 0.0.0.0 --port %PORT%
)