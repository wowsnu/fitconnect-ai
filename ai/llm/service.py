"""
LLM integration service for FitConnect Backend
Supports OpenAI GPT and Anthropic Claude
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

import openai
from openai import OpenAI
import httpx
from pydantic import BaseModel

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """LLM response model"""
    content: str
    provider: LLMProvider
    model: str
    usage: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class LLMService:
    """LLM integration service"""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize LLM clients"""
        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

        # Initialize Anthropic client (using httpx for API calls)
        if settings.ANTHROPIC_API_KEY:
            try:
                self.anthropic_client = httpx.AsyncClient(
                    headers={
                        "x-api-key": settings.ANTHROPIC_API_KEY,
                        "content-type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    base_url="https://api.anthropic.com"
                )
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")

    async def generate_completion(
        self,
        messages: List[ChatMessage],
        provider: LLMProvider = LLMProvider.OPENAI,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using specified LLM provider

        Args:
            messages: List of chat messages
            provider: LLM provider to use
            model: Model name (provider-specific)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse object
        """
        if provider == LLMProvider.OPENAI:
            return await self._openai_completion(messages, model, temperature, max_tokens, **kwargs)
        elif provider == LLMProvider.ANTHROPIC:
            return await self._anthropic_completion(messages, model, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _openai_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenAI"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        if model is None:
            model = "gpt-3.5-turbo"

        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            response = self.openai_client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                provider=LLMProvider.OPENAI,
                model=model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id
                }
            )

        except Exception as e:
            logger.error(f"OpenAI completion error: {e}")
            raise ValueError(f"OpenAI completion failed: {str(e)}")

    async def _anthropic_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Anthropic Claude"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized. Check API key.")

        if model is None:
            model = "claude-3-haiku-20240307"

        try:
            # Convert messages to Anthropic format
            system_message = None
            anthropic_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    anthropic_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": anthropic_messages,
                **kwargs
            }

            if system_message:
                payload["system"] = system_message

            response = await self.anthropic_client.post("/v1/messages", json=payload)
            response.raise_for_status()

            data = response.json()

            return LLMResponse(
                content=data["content"][0]["text"],
                provider=LLMProvider.ANTHROPIC,
                model=model,
                usage={
                    "input_tokens": data["usage"]["input_tokens"],
                    "output_tokens": data["usage"]["output_tokens"],
                    "total_tokens": data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                },
                metadata={
                    "stop_reason": data.get("stop_reason"),
                    "response_id": data.get("id")
                }
            )

        except Exception as e:
            logger.error(f"Anthropic completion error: {e}")
            raise ValueError(f"Anthropic completion failed: {str(e)}")

    async def analyze_candidate_profile(self, profile_text: str) -> Dict[str, Any]:
        """
        Analyze candidate profile and extract key competencies

        Args:
            profile_text: Candidate profile text (resume, interview transcript, etc.)

        Returns:
            Dictionary containing analyzed competencies and skills
        """
        system_prompt = """
        당신은 채용 전문가입니다. 제공된 지원자 프로필을 분석하여 핵심 역량을 추출하고 구조화해주세요.

        다음 항목들을 분석해주세요:
        1. 기술 스킬 (Technical Skills)
        2. 소프트 스킬 (Soft Skills)
        3. 경력 레벨 (Experience Level)
        4. 주요 성과 (Key Achievements)
        5. 성장 잠재력 (Growth Potential)

        결과는 JSON 형식으로 구조화해서 반환해주세요.
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"분석할 프로필:\n{profile_text}")
        ]

        try:
            response = await self.generate_completion(
                messages=messages,
                provider=LLMProvider.OPENAI,
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=1500
            )

            # Try to parse as JSON, fallback to text analysis
            try:
                import json
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                analysis = {"analysis": response.content}

            return analysis

        except Exception as e:
            logger.error(f"Profile analysis error: {e}")
            raise ValueError(f"Profile analysis failed: {str(e)}")

    async def analyze_job_posting(self, job_posting_text: str) -> Dict[str, Any]:
        """
        Analyze job posting and extract requirements

        Args:
            job_posting_text: Job posting description

        Returns:
            Dictionary containing analyzed requirements and preferences
        """
        system_prompt = """
        당신은 채용 전문가입니다. 제공된 채용 공고를 분석하여 요구사항을 추출하고 구조화해주세요.

        다음 항목들을 분석해주세요:
        1. 필수 기술 스킬 (Required Technical Skills)
        2. 우대 기술 스킬 (Preferred Technical Skills)
        3. 경력 요구사항 (Experience Requirements)
        4. 소프트 스킬 요구사항 (Soft Skills Requirements)
        5. 회사 문화 및 환경 (Company Culture & Environment)

        결과는 JSON 형식으로 구조화해서 반환해주세요.
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=f"분석할 채용공고:\n{job_posting_text}")
        ]

        try:
            response = await self.generate_completion(
                messages=messages,
                provider=LLMProvider.OPENAI,
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=1500
            )

            # Try to parse as JSON, fallback to text analysis
            try:
                import json
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                analysis = {"analysis": response.content}

            return analysis

        except Exception as e:
            logger.error(f"Job posting analysis error: {e}")
            raise ValueError(f"Job posting analysis failed: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """Check health status of LLM service"""
        status = {
            "service": "healthy",
            "providers": {
                "openai": self.openai_client is not None,
                "anthropic": self.anthropic_client is not None
            }
        }

        if not any(status["providers"].values()):
            status["service"] = "no_providers_available"

        return status


# Global LLM service instance
llm_service = LLMService()