"""
API routes for FitConnect Backend
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
        "version": "1.0.0"
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