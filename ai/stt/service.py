"""
Pure Python STT service - 완전 독립적인 AI 모듈
FastAPI 의존성 없음, 순수 Python 함수들
"""

import os
import tempfile
import logging
from typing import Optional, Tuple, Dict, Any, Union
from pathlib import Path
import io

import whisper
import torch

logger = logging.getLogger(__name__)


class PureSTTService:
    """순수 Python STT 서비스 - 웹 프레임워크 의존성 없음"""

    def __init__(self, model_name: str = "base", device: Optional[str] = None):
        """
        Args:
            model_name: Whisper 모델명 (tiny, base, small, medium, large)
            device: 디바이스 ("cpu", "cuda", auto-detect)
        """
        self.model = None
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"PureSTT Service initialized - Model: {model_name}, Device: {self.device}")

    def load_model(self, model_name: Optional[str] = None) -> None:
        """Whisper 모델 로드"""
        model_to_load = model_name or self.model_name

        try:
            logger.info(f"Loading Whisper model: {model_to_load}")
            self.model = whisper.load_model(model_to_load, device=self.device)
            self.model_name = model_to_load
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Failed to load STT model: {str(e)}")

    def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = "ko"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        파일 경로로 음성 파일 전사

        Args:
            file_path: 오디오 파일 경로
            language: 언어 코드 (ko, en, auto 등)

        Returns:
            (transcribed_text, metadata)
        """
        if self.model is None:
            self.load_model()

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # 지원 포맷 확인
        supported_formats = [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"]
        file_extension = Path(file_path).suffix.lower()

        if file_extension not in supported_formats:
            raise ValueError(f"Unsupported format: {file_extension}. Supported: {supported_formats}")

        try:
            logger.info(f"Transcribing file: {file_path}")
            result = self.model.transcribe(
                file_path,
                language=language if language != "auto" else None,
                task="transcribe",
                verbose=False
            )

            transcribed_text = result["text"].strip()

            metadata = {
                "language": result.get("language", language),
                "duration": result.get("duration", 0.0),
                "segments_count": len(result.get("segments", [])),
                "confidence": self._calculate_confidence(result.get("segments", [])),
                "file_path": file_path
            }

            logger.info(f"Transcription completed: {transcribed_text[:50]}...")
            return transcribed_text, metadata

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {str(e)}")

    def transcribe_bytes(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = "ko"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        바이트 데이터로 음성 전사 (파일 업로드 대응)

        Args:
            audio_data: 오디오 파일 바이트 데이터
            filename: 원본 파일명 (확장자 확인용)
            language: 언어 코드

        Returns:
            (transcribed_text, metadata)
        """
        file_extension = Path(filename).suffix.lower()

        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_extension
        ) as tmp_file:
            try:
                tmp_file.write(audio_data)
                tmp_file.flush()

                return self.transcribe_file(tmp_file.name, language)

            finally:
                # 임시 파일 정리
                try:
                    if os.path.exists(tmp_file.name):
                        os.unlink(tmp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file: {e}")

    def transcribe_stream(
        self,
        audio_stream: Union[io.BytesIO, io.BufferedReader],
        filename: str = "stream.wav",
        language: Optional[str] = "ko"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        스트림에서 음성 전사

        Args:
            audio_stream: 오디오 스트림
            filename: 파일명 (확장자 확인용)
            language: 언어 코드

        Returns:
            (transcribed_text, metadata)
        """
        audio_data = audio_stream.read()
        return self.transcribe_bytes(audio_data, filename, language)

    def _calculate_confidence(self, segments: list) -> float:
        """세그먼트에서 신뢰도 계산"""
        if not segments:
            return 0.0

        # Whisper는 직접적인 confidence 제공하지 않음
        # 세그먼트 길이와 일관성으로 추정
        if len(segments) > 0:
            avg_length = sum(len(seg.get("text", "")) for seg in segments) / len(segments)
            return min(0.95, 0.7 + (avg_length / 100))

        return 0.85

    def get_supported_formats(self) -> list:
        """지원하는 오디오 포맷 반환"""
        return [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"]

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "model_loaded": self.model is not None,
            "supported_formats": self.get_supported_formats()
        }

    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "service": "STT",
            "status": "healthy" if self.model is not None else "model_not_loaded",
            "model_info": self.get_model_info(),
            "whisper_available": True
        }


# 편의를 위한 전역 인스턴스 및 함수들
_default_stt_service = None

def get_stt_service() -> PureSTTService:
    """기본 STT 서비스 인스턴스 반환"""
    global _default_stt_service
    if _default_stt_service is None:
        _default_stt_service = PureSTTService()
    return _default_stt_service

def transcribe_audio_file(
    file_path: str,
    language: str = "ko"
) -> Tuple[str, Dict[str, Any]]:
    """간단한 파일 전사 함수"""
    service = get_stt_service()
    return service.transcribe_file(file_path, language)

def transcribe_audio_bytes(
    audio_data: bytes,
    filename: str = "audio.wav",
    language: str = "ko"
) -> Tuple[str, Dict[str, Any]]:
    """간단한 바이트 전사 함수"""
    service = get_stt_service()
    return service.transcribe_bytes(audio_data, filename, language)


if __name__ == "__main__":
    # 테스트 코드
    import sys

    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        try:
            text, metadata = transcribe_audio_file(audio_file)
            print(f"Transcription: {text}")
            print(f"Metadata: {metadata}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        # 서비스 상태 확인
        service = get_stt_service()
        print(service.health_check())