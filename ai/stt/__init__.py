"""Speech-to-Text module for FitConnect Backend"""

from .service import stt_service, STTService
from .routes import stt_router
from .models import TranscriptionResponse, TranscriptionRequest, STTHealthResponse

__all__ = [
    "stt_service",
    "STTService",
    "stt_router",
    "TranscriptionResponse",
    "TranscriptionRequest",
    "STTHealthResponse"
]