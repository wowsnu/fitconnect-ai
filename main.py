"""
FitConnect Backend - Main Application Entry Point
AI-powered recruitment matching platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.routes import ai_router
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="FitConnect Backend",
    description="AI-powered recruitment matching platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI routes
app.include_router(ai_router, prefix="/api/ai", tags=["AI"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "FitConnect Backend is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )