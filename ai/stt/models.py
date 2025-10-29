"""
Pydantic models for STT module
"""

from typing import Optional
from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    """Response model for transcription"""
    text: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Detected or specified language")
    duration: float = Field(..., description="Audio duration in seconds")
    segments_count: int = Field(..., description="Number of speech segments")
    confidence: float = Field(..., description="Confidence score (0-1)")


class TranscriptionRequest(BaseModel):
    """Request model for transcription configuration"""
    language: Optional[str] = Field("ko", description="Language code (ko, en, etc.)")
    model_size: Optional[str] = Field("base", description="Whisper model size")


class STTHealthResponse(BaseModel):
    """Health check response for STT service"""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    device: str = Field(..., description="Compute device (cpu/cuda)")


class AudioUploadLimits(BaseModel):
    """Audio upload limits information"""
    max_file_size_mb: int = Field(..., description="Maximum file size in MB")
    max_duration_minutes: int = Field(..., description="Maximum duration in minutes")
    supported_formats: list[str] = Field(..., description="Supported audio formats")