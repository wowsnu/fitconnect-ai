"""
Pure Python LLM service - 완전 독립적인 AI 모듈
OpenAI, Anthropic 등 LLM 통합 서비스
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import os

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """지원하는 LLM 프로바이더"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ChatMessage:
    """채팅 메시지"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM 응답"""
    content: str
    provider: str
    model: str
    usage: Dict[str, Any]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PureLLMService:
    """순수 Python LLM 서비스"""

    def __init__(self, openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        """
        Args:
            openai_api_key: OpenAI API 키 (None이면 환경변수에서)
            anthropic_api_key: Anthropic API 키 (None이면 환경변수에서)
        """
        self.openai_client = None
        self.anthropic_client = None

        self._setup_openai(openai_api_key)
        self._setup_anthropic(anthropic_api_key)

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

    def _setup_anthropic(self, api_key: Optional[str] = None):
        """Anthropic 클라이언트 설정"""
        try:
            # Anthropic 클라이언트는 필요시 나중에 추가
            key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if key:
                logger.info("Anthropic API key available (client not implemented yet)")
            else:
                logger.warning("Anthropic API key not found")
        except Exception as e:
            logger.error(f"Failed to setup Anthropic client: {e}")

    def generate_completion(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        텍스트 생성

        Args:
            messages: 메시지 리스트
            provider: LLM 프로바이더 ("openai", "anthropic")
            model: 사용할 모델명
            temperature: 창의성 조절 (0.0-1.0)
            max_tokens: 최대 토큰 수
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse 객체
        """
        if provider == "openai":
            return self._generate_openai(messages, model, temperature, max_tokens, **kwargs)
        elif provider == "anthropic":
            return self._generate_anthropic(messages, model, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _generate_openai(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
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

            return LLMResponse(
                content=response.choices[0].message.content,
                provider="openai",
                model=model_name,
                usage=usage,
                metadata={"finish_reason": response.choices[0].finish_reason}
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")

    def _generate_anthropic(self, messages, model, temperature, max_tokens, **kwargs):
        """Anthropic 텍스트 생성 (향후 구현)"""
        raise NotImplementedError("Anthropic integration not implemented yet")

    def analyze_candidate_profile(self, profile_text: str, **kwargs) -> Dict[str, Any]:
        """
        지원자 프로필 분석

        Args:
            profile_text: 지원자 프로필 텍스트
            **kwargs: 추가 LLM 파라미터

        Returns:
            분석 결과 딕셔너리
        """
        system_prompt = """
        당신은 채용 전문가입니다. 제공된 지원자 프로필을 분석하여 다음 항목들을 추출하고 구조화해주세요:

        1. 기술 스킬 (Technical Skills): 프로그래밍 언어, 프레임워크, 도구 등
        2. 소프트 스킬 (Soft Skills): 커뮤니케이션, 리더십, 팀워크 등
        3. 경력 레벨 (Experience Level): 신입, 주니어, 시니어 등
        4. 전문 분야 (Expertise): 프론트엔드, 백엔드, 풀스택, 데이터 등
        5. 성장 잠재력 (Growth Potential): 학습 의지, 적응력 등

        JSON 형식으로 구조화된 결과를 반환해주세요.
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"분석할 프로필:\n{profile_text}")
        ]

        try:
            response = self.generate_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=800,
                **kwargs
            )

            # JSON 파싱 시도
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # JSON 파싱 실패시 텍스트 그대로 반환
                analysis = {"raw_analysis": response.content}

            return analysis

        except Exception as e:
            logger.error(f"Profile analysis failed: {e}")
            return {"error": f"분석 중 오류 발생: {str(e)}"}

    def analyze_job_posting(self, job_text: str, **kwargs) -> Dict[str, Any]:
        """
        채용 공고 분석

        Args:
            job_text: 채용 공고 텍스트
            **kwargs: 추가 LLM 파라미터

        Returns:
            분석 결과 딕셔너리
        """
        system_prompt = """
        당신은 채용 컨설턴트입니다. 제공된 채용 공고를 분석하여 다음을 구조화해주세요:

        1. 필수 기술 스킬 (Required Skills)
        2. 우대 기술 스킬 (Preferred Skills)
        3. 경력 요구사항 (Experience Requirements)
        4. 업무 내용 (Job Responsibilities)
        5. 회사 문화/혜택 (Company Culture & Benefits)
        6. 근무 조건 (Work Conditions)

        JSON 형식으로 구조화된 결과를 반환해주세요.
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"분석할 채용공고:\n{job_text}")
        ]

        try:
            response = self.generate_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=800,
                **kwargs
            )

            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                analysis = {"raw_analysis": response.content}

            return analysis

        except Exception as e:
            logger.error(f"Job posting analysis failed: {e}")
            return {"error": f"분석 중 오류 발생: {str(e)}"}

    def generate_interview_questions(
        self,
        context: str,
        question_count: int = 5,
        interview_type: str = "general",
        **kwargs
    ) -> List[str]:
        """
        면접 질문 생성

        Args:
            context: 면접 맥락 (직무, 요구사항 등)
            question_count: 생성할 질문 수
            interview_type: 면접 유형 ("technical", "behavioral", "general")
            **kwargs: 추가 LLM 파라미터

        Returns:
            질문 리스트
        """
        system_prompt = f"""
        당신은 면접관입니다. 주어진 컨텍스트를 바탕으로 {interview_type} 면접 질문을 {question_count}개 생성해주세요.

        질문 유형별 가이드라인:
        - technical: 기술적 역량과 문제해결 능력을 평가하는 질문
        - behavioral: 경험과 행동 패턴을 파악하는 질문
        - general: 일반적인 적합성과 동기를 확인하는 질문

        각 질문은 구체적이고 답변을 통해 의미있는 평가가 가능해야 합니다.
        질문만 나열해주세요 (번호 포함).
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"컨텍스트:\n{context}")
        ]

        try:
            response = self.generate_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=600,
                **kwargs
            )

            # 질문들을 파싱
            questions = []
            lines = response.content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # 번호나 불릿 포인트 제거
                    question = line.lstrip('0123456789.- ').strip()
                    if question:
                        questions.append(question)

            return questions[:question_count]

        except Exception as e:
            logger.error(f"Interview question generation failed: {e}")
            return [f"질문 생성 중 오류가 발생했습니다: {str(e)}"]

    def get_available_models(self, provider: str = "openai") -> List[str]:
        """사용 가능한 모델 리스트"""
        if provider == "openai":
            return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        elif provider == "anthropic":
            return ["claude-3-5-sonnet-20241022", "claude-3-sonnet", "claude-3-opus"]
        else:
            return []

    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        return {
            "service": "LLM",
            "status": "healthy",
            "providers": {
                "openai": self.openai_client is not None,
                "anthropic": False  # 미구현
            },
            "available_models": {
                "openai": self.get_available_models("openai") if self.openai_client else [],
                "anthropic": self.get_available_models("anthropic")
            }
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

def analyze_profile(profile_text: str) -> Dict[str, Any]:
    """간단한 프로필 분석"""
    service = get_llm_service()
    return service.analyze_candidate_profile(profile_text)

def analyze_job(job_text: str) -> Dict[str, Any]:
    """간단한 채용공고 분석"""
    service = get_llm_service()
    return service.analyze_job_posting(job_text)


if __name__ == "__main__":
    # 테스트 코드
    service = get_llm_service()
    print(service.health_check())