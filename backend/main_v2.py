import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from utils.database import init_db
from routes.user_routes import router as user_router
from routes.admin_routes import router as admin_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Smart Farmer API",
    description="Backend API for Smart Farmer mobile application and admin dashboard",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost",
        "https://farmerlk.me",
        "https://www.farmerlk.me",
        "*"  # Remove in production and specify exact origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables on application startup"""
    init_db()
    print("✓ Database initialized successfully")

# Health check endpoints
@app.get("/")
def root():
    """Root endpoint - API status check"""
    return {
        "message": "Smart Farmer Backend API is running!",
        "version": "2.0.0",
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "smart-farmer-api"
    }

# Include routers
app.include_router(user_router)
app.include_router(admin_router)

# Entry point for local development
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Enable auto-reload during development
    )
