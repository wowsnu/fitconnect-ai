"""
FastAPI routes for Speech-to-Text functionality
"""

import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from .service import stt_service
from .models import (
    TranscriptionResponse,
    STTHealthResponse,
    AudioUploadLimits
)
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

stt_router = APIRouter()


@stt_router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
    language: Optional[str] = Form("ko", description="Language code (ko, en, etc.)")
):
    """
    Transcribe uploaded audio file to text

    - **audio_file**: Audio file (WAV, MP3, M4A, OGG, WEBM)
    - **language**: Language code (default: ko for Korean)
    """
    try:
        # Check file size
        if audio_file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Transcribe audio
        text, metadata = await stt_service.transcribe_audio(audio_file, language)

        return TranscriptionResponse(
            text=text,
            language=metadata["language"],
            duration=metadata["duration"],
            segments_count=metadata["segments_count"],
            confidence=metadata["confidence"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@stt_router.get("/health", response_model=STTHealthResponse)
async def stt_health_check():
    """
    Check STT service health status
    """
    try:
        model_loaded = stt_service.model is not None
        device = stt_service.device

        return STTHealthResponse(
            status="healthy" if model_loaded else "model_not_loaded",
            model_loaded=model_loaded,
            device=device
        )
    except Exception as e:
        logger.error(f"STT health check error: {e}")
        return STTHealthResponse(
            status="error",
            model_loaded=False,
            device="unknown"
        )


@stt_router.post("/load-model")
async def load_stt_model(model_name: Optional[str] = None):
    """
    Load or reload STT model

    - **model_name**: Whisper model name (tiny, base, small, medium, large)
    """
    try:
        stt_service.load_model(model_name)
        return {"message": f"Model {model_name or settings.WHISPER_MODEL} loaded successfully"}
    except Exception as e:
        logger.error(f"Model loading error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@stt_router.get("/limits", response_model=AudioUploadLimits)
async def get_upload_limits():
    """
    Get audio upload limits and supported formats
    """
    return AudioUploadLimits(
        max_file_size_mb=settings.MAX_FILE_SIZE // (1024 * 1024),
        max_duration_minutes=10,  # 10 minutes max
        supported_formats=["audio/wav", "audio/mp3", "audio/m4a", "audio/ogg", "audio/webm"]
    )


@stt_router.get("/")
async def stt_info():
    """
    STT module information
    """
    return {
        "module": "Speech-to-Text",
        "description": "Convert speech audio to text using OpenAI Whisper",
        "model": settings.WHISPER_MODEL,
        "device": stt_service.device,
        "endpoints": {
            "POST /transcribe": "Transcribe audio file to text",
            "GET /health": "Check service health",
            "POST /load-model": "Load/reload STT model",
            "GET /limits": "Get upload limits and formats"
        }
    }