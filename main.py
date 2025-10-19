"""
FitConnect Backend - Main Application Entry Point
AI-powered recruitment matching platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.routes import api_router
from api.interview_routes import interview_router
from api.company_interview_routes import company_interview_router
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="FitConnect Backend",
    description="AI-powered recruitment matching platform",
    version="1.0.0"
)

# CORS middleware configuration
# Origins can be configured via BACKEND_CORS_ORIGINS in .env or environment variables
# Format: BACKEND_CORS_ORIGINS=["http://localhost:3000","https://yourapp.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,  # Only safe because we use explicit origins
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routes
app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(interview_router, prefix="/api")
app.include_router(company_interview_router, prefix="/api")

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