"""
API routes for FitConnect Backend
"""

from fastapi import APIRouter

# Import AI module routers
from ai.stt.routes import stt_router
from ai.llm.routes import llm_router
from ai.interview.routes import interview_router

# Create main AI router
ai_router = APIRouter()

@ai_router.get("/")
async def ai_root():
    """AI module root endpoint"""
    return {
        "message": "FitConnect AI Module",
        "version": "1.0.0",
        "available_endpoints": [
            "/stt - Speech-to-Text functionality",
            "/llm - LLM integration",
            "/interview - AI Interview system"
        ],
        "health_checks": [
            "/stt/health",
            "/llm/health",
            "/interview/health"
        ]
    }

# Include AI sub-routers
ai_router.include_router(stt_router, prefix="/stt", tags=["Speech-to-Text"])
ai_router.include_router(llm_router, prefix="/llm", tags=["Large Language Models"])
ai_router.include_router(interview_router, prefix="/interview", tags=["AI Interview"])