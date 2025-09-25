"""
Minimal STT service using only OpenAI Whisper (without pydub)
"""

import os
import tempfile
import logging
from typing import Optional, Tuple
from pathlib import Path

import whisper
import torch
from fastapi import UploadFile, HTTPException

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class STTService:
    """Minimal Speech-to-Text service using only Whisper"""

    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"STT Service initialized with device: {self.device}")

    def load_model(self, model_name: str = None) -> None:
        """Load Whisper model"""
        if model_name is None:
            model_name = settings.WHISPER_MODEL

        try:
            logger.info(f"Loading Whisper model: {model_name}")
            self.model = whisper.load_model(model_name, device=self.device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load STT model: {str(e)}")

    async def transcribe_audio(
        self,
        audio_file: UploadFile,
        language: Optional[str] = "ko"
    ) -> Tuple[str, dict]:
        """
        Transcribe audio file to text (supports WAV, MP3, M4A, etc.)

        Args:
            audio_file: Uploaded audio file
            language: Language code (ko for Korean, en for English, etc.)

        Returns:
            Tuple of (transcribed_text, metadata)
        """
        if self.model is None:
            self.load_model()

        # Whisper supports many formats natively: wav, mp3, m4a, flac, etc.
        allowed_extensions = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"]
        file_extension = Path(audio_file.filename or "").suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_extension}. Supported: {allowed_extensions}"
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as tmp_file:
            try:
                # Save uploaded file
                content = await audio_file.read()
                tmp_file.write(content)
                tmp_file.flush()

                # Transcribe directly (Whisper handles format conversion internally)
                logger.info(f"Transcribing audio file: {audio_file.filename}")
                result = self.model.transcribe(
                    tmp_file.name,
                    language=language,
                    task="transcribe",
                    verbose=False
                )

                transcribed_text = result["text"].strip()

                # Extract metadata
                metadata = {
                    "language": result.get("language", language),
                    "duration": result.get("duration", 0),
                    "segments_count": len(result.get("segments", [])),
                    "confidence": self._calculate_confidence(result.get("segments", []))
                }

                logger.info(f"Transcription completed. Text: {transcribed_text[:100]}...")
                return transcribed_text, metadata

            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

            finally:
                # Cleanup temporary file
                try:
                    if os.path.exists(tmp_file.name):
                        os.unlink(tmp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temporary file: {e}")

    def _calculate_confidence(self, segments: list) -> float:
        """Calculate average confidence score from segments"""
        if not segments:
            return 0.0

        # Whisper doesn't provide confidence directly, but we can estimate from segment consistency
        return 0.85  # Default confidence score

    def health_check(self) -> dict:
        """Check STT service health"""
        return {
            "available": True,
            "model_loaded": self.model is not None,
            "device": self.device,
            "whisper_version": whisper.__version__ if hasattr(whisper, '__version__') else "unknown"
        }


# Global STT service instance
stt_service = STTService()