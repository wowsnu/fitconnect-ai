"""
FitConnect AI Service - Independent AI Service
Handles all AI-related functionality (STT, LLM, Interview)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import AI module routers
from ai.stt.routes import stt_router
from ai.llm.routes import llm_router
from ai.interview.routes import interview_router

from config import get_settings

settings = get_settings()

app = FastAPI(
    title="FitConnect AI Service",
    description="AI service for FitConnect - handles STT, LLM, and Interview AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI routes directly
app.include_router(stt_router, prefix="/stt", tags=["Speech-to-Text"])
app.include_router(llm_router, prefix="/llm", tags=["Large Language Models"])
app.include_router(interview_router, prefix="/interview", tags=["AI Interview"])

@app.get("/")
async def ai_service_root():
    """AI Service root endpoint"""
    return {
        "service": "FitConnect AI Service",
        "version": "1.0.0",
        "available_endpoints": [
            "/stt - Speech-to-Text functionality",
            "/llm - LLM integration",
            "/interview - AI Interview system"
        ]
    }

@app.get("/health")
async def ai_health_check():
    """AI Service health check"""
    return {"service": "ai", "status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "ai_service:app",
        host="0.0.0.0",
        port=8001,  # AI service runs on port 8001
        reload=True
    )