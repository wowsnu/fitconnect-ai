"""
API routes for FitConnect Backend
Note: AI services are now pure Python libraries, not HTTP endpoints
Backend should import and use them directly:

from ai.stt.service import get_stt_service
from ai.llm.service import get_llm_service
from ai.embedding.service import get_embedding_service
from ai.matching.service import get_matching_service
"""

from fastapi import APIRouter, UploadFile, File, Form, WebSocket
from ai.stt.service import transcribe_audio_bytes, PureSTTService
from ai.stt.models import TranscriptionResponse
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

@api_router.post("/stt/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("ko")
):
    """음성 파일을 받아 텍스트로 변환"""
    audio_bytes = await file.read()
    text, metadata = transcribe_audio_bytes(audio_bytes, filename=file.filename, language=language)
    
    return TranscriptionResponse(
        text=text,
        language=metadata.get("language", language),
        duration=metadata.get("duration", 0.0),
        segments_count=metadata.get("segments_count", 0),
        confidence=metadata.get("confidence", 0.0)
    )