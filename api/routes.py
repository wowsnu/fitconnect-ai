"""
API routes for FitConnect Backend
Note: AI services are now pure Python libraries, not HTTP endpoints
Backend should import and use them directly:

from ai.stt.service import get_stt_service
from ai.llm.service import get_llm_service
from ai.embedding.service import get_embedding_service
from ai.matching.service import get_matching_service
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

@api_router.get("/")
async def api_root():
    """API module root endpoint"""
    return {
        "message": "FitConnect API",
        "version": "1.0.0",
        "note": "AI services are now pure Python libraries",
        "usage": {
            "stt": "from ai.stt.service import get_stt_service",
            "llm": "from ai.llm.service import get_llm_service",
            "embedding": "from ai.embedding.service import get_embedding_service",
            "matching": "from ai.matching.service import get_matching_service"
        }
    }