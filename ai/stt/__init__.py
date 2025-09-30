"""Speech-to-Text module for FitConnect Backend"""

from .service import get_stt_service, PureSTTService
from .models import TranscriptionResponse, TranscriptionRequest, STTHealthResponse

__all__ = [
    "get_stt_service",
    "PureSTTService",
    "TranscriptionResponse",
    "TranscriptionRequest",
    "STTHealthResponse"
]