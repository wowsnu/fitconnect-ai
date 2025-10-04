"""
Pure Python LLM service - 완전 독립적인 AI 모듈
OpenAI GPT 통합 서비스
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
import os
from pathlib import Path

from openai import OpenAI

from .models import ChatMessage, CompletionResponse
from . import prompts
from ..stt.service import get_stt_service

logger = logging.getLogger(__name__)


class PureLLMService:
    """순수 Python LLM 서비스"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Args:
            openai_api_key: OpenAI API 키 (None이면 환경변수에서)
        """
        self.openai_client = None
        self._setup_openai(openai_api_key)

    def _setup_openai(self, api_key: Optional[str] = None):
        """OpenAI 클라이언트 설정"""
        try:
            key = api_key or os.getenv("OPENAI_API_KEY")
            if key:
                self.openai_client = OpenAI(api_key=key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not found")
        except Exception as e:
            logger.error(f"Failed to setup OpenAI client: {e}")

    def generate_completion(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> CompletionResponse:
        """
        텍스트 생성 (OpenAI)

        Args:
            messages: 메시지 리스트
            model: 사용할 모델명 (기본: gpt-4o)
            temperature: 창의성 조절 (0.0-1.0)
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터

        Returns:
            CompletionResponse 객체
        """
        return self._generate_openai(messages, model, temperature, max_tokens, **kwargs)

    def _generate_openai(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> CompletionResponse:
        """OpenAI 텍스트 생성"""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        # 메시지 형식 변환
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                raise TypeError(f"Invalid message type: {type(msg)}")

        try:
            model_name = model or "gpt-4o"

            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            return CompletionResponse(
                content=response.choices[0].message.content,
                provider="openai",
                model=model_name,
                usage=usage,
                metadata={"finish_reason": response.choices[0].finish_reason}
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")

    def analyze_interview(
        self,
        audio_data: bytes,
        filename: str = "interview.wav",
        language: str = "ko",
        **kwargs
    ) -> Dict[str, Any]:
        """
        면접 음성 파일 분석 (STT → LLM 분석)

        Args:
            audio_data: 음성 파일 바이트 데이터
            filename: 파일명 (확장자 확인용)
            language: 언어 코드 (ko, en 등)
            **kwargs: 추가 LLM 파라미터

        Returns:
            {
                "transcript": "면접 텍스트",
                "analysis": {...},  # 면접 분석 결과
                "stt_metadata": {...}
            }
        """
        try:
            # 1. STT: 음성 → 텍스트 (텍스트 입력은 우회)
            file_extension = Path(filename).suffix.lower()
            stt_metadata: Dict[str, Any]

            if file_extension == ".txt":
                transcript = audio_data.decode("utf-8", errors="ignore").strip()
                stt_metadata = {
                    "source": "text_input",
                    "language": language,
                    "filename": filename,
                    "bytes": len(audio_data)
                }
            else:
                stt_service = get_stt_service()
                supported_formats = getattr(stt_service, "get_supported_formats", lambda: [])()

                if supported_formats and file_extension not in supported_formats:
                    transcript = audio_data.decode("utf-8", errors="ignore").strip()
                    stt_metadata = {
                        "source": "text_input_fallback",
                        "language": language,
                        "filename": filename,
                        "bytes": len(audio_data)
                    }
                else:
                    transcript, stt_metadata = stt_service.transcribe_bytes(
                        audio_data=audio_data,
                        filename=filename,
                        language=language
                    )

            logger.info(f"STT completed: {transcript[:50]}...")

            # 2. LLM: 면접 분석 (prompts.py 사용)
            messages = prompts.build_interview_analysis_messages(transcript)

            response = self.generate_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
                **kwargs
            )

            # 3. JSON 파싱
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                analysis = {"raw_analysis": response.content}

            return {
                "transcript": transcript,
                "analysis": analysis,
                "stt_metadata": stt_metadata
            }

        except Exception as e:
            logger.error(f"Interview analysis failed: {e}")
            return {"error": f"면접 분석 중 오류 발생: {str(e)}"}

    def integrate_profile(
        self,
        db_profile: Dict[str, Any],
        interview_analysis: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        DB 프로필 + 면접 분석 통합

        Args:
            db_profile: DB에서 가져온 구조화된 프로필 데이터
            interview_analysis: 면접 분석 결과
            **kwargs: 추가 LLM 파라미터

        Returns:
            통합된 최종 프로필 분석 결과
        """
        try:
            # prompts.py의 통합 프롬프트 사용
            messages = prompts.build_integration_messages(db_profile, interview_analysis)

            response = self.generate_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1200,
                **kwargs
            )

            # JSON 파싱
            try:
                integrated_profile = json.loads(response.content)
            except json.JSONDecodeError:
                integrated_profile = {"raw_analysis": response.content}

            return integrated_profile

        except Exception as e:
            logger.error(f"Profile integration failed: {e}")
            return {"error": f"프로필 통합 중 오류 발생: {str(e)}"}

    def create_complete_profile(
        self,
        audio_data: bytes,
        db_profile: Dict[str, Any],
        filename: str = "interview.wav",
        language: str = "ko",
        **kwargs
    ) -> Dict[str, Any]:
        """
        전체 플로우: 면접 분석 → DB 통합 → 임베딩 생성

        Args:
            audio_data: 면접 음성 파일 바이트 데이터
            db_profile: DB 프로필 데이터
            filename: 파일명
            language: 언어 코드
            **kwargs: 추가 LLM 파라미터

        Returns:
            {
                "transcript": "면접 텍스트",
                "interview_analysis": {...},
                "integrated_profile": {...},
                "embedding_vector": {...},
                "stt_metadata": {...}
            }
        """
        try:
            # 1. 면접 분석 (STT → LLM)
            interview_result = self.analyze_interview(
                audio_data=audio_data,
                filename=filename,
                language=language,
                **kwargs
            )

            if "error" in interview_result:
                return interview_result

            # 2. DB + 면접 통합
            integrated_profile = self.integrate_profile(
                db_profile=db_profile,
                interview_analysis=interview_result["analysis"],
                **kwargs
            )

            if "error" in integrated_profile:
                return integrated_profile

            # 3. 임베딩 생성
            from ..embedding.service import get_embedding_service
            embedding_service = get_embedding_service()

            # 선호도와 스킬 추출
            work_preferences = integrated_profile.get("work_preferences", "")
            technical_skills = integrated_profile.get("technical_skills", [])
            tools = integrated_profile.get("tools_and_platforms", [])
            soft_skills = integrated_profile.get("soft_skills", [])

            skills_text = ", ".join(technical_skills + tools + soft_skills)

            vector_result = embedding_service.create_applicant_vector(
                preferences=work_preferences,
                skills=skills_text
            )

            # 4. 전체 결과 반환
            return {
                "transcript": interview_result["transcript"],
                "interview_analysis": interview_result["analysis"],
                "integrated_profile": integrated_profile,
                "embedding_vector": vector_result.combined_vector,
                "vector_metadata": {
                    "model": vector_result.model,
                    "dimension": vector_result.dimension
                },
                "stt_metadata": interview_result["stt_metadata"]
            }

        except Exception as e:
            logger.error(f"Complete profile creation failed: {e}")
            return {"error": f"전체 프로필 생성 중 오류 발생: {str(e)}"}

    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "service": "LLM",
            "status": "healthy" if self.openai_client else "not_configured",
            "openai_configured": self.openai_client is not None
        }


# 편의 함수들
_default_llm_service = None

def get_llm_service() -> PureLLMService:
    """기본 LLM 서비스 인스턴스 반환"""
    global _default_llm_service
    if _default_llm_service is None:
        _default_llm_service = PureLLMService()
    return _default_llm_service

def generate_text(prompt: str, **kwargs) -> str:
    """간단한 텍스트 생성"""
    service = get_llm_service()
    messages = [ChatMessage(role="user", content=prompt)]
    response = service.generate_completion(messages, **kwargs)
    return response.content

def analyze_interview_audio(
    audio_data: bytes,
    filename: str = "interview.wav",
    language: str = "ko"
) -> Dict[str, Any]:
    """면접 음성 분석 편의 함수"""
    service = get_llm_service()
    return service.analyze_interview(audio_data, filename, language)

def integrate_candidate_profile(
    db_profile: Dict[str, Any],
    interview_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """프로필 통합 편의 함수"""
    service = get_llm_service()
    return service.integrate_profile(db_profile, interview_analysis)

def create_complete_candidate_profile(
    audio_data: bytes,
    db_profile: Dict[str, Any],
    filename: str = "interview.wav",
    language: str = "ko"
) -> Dict[str, Any]:
    """전체 플로우 편의 함수: 면접→통합→임베딩"""
    service = get_llm_service()
    return service.create_complete_profile(audio_data, db_profile, filename, language)


if __name__ == "__main__":
    # 테스트 코드
    service = get_llm_service()
    print(service.health_check())
