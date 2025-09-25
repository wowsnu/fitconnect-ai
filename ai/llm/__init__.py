"""Large Language Model integration module for FitConnect Backend"""

from .service import llm_service, LLMService, LLMProvider
from .routes import llm_router
from .models import (
    ChatMessage,
    CompletionRequest,
    CompletionResponse,
    ProfileAnalysisRequest,
    JobAnalysisRequest,
    LLMHealthResponse,
    SkillAnalysis,
    JobRequirements
)

__all__ = [
    "llm_service",
    "LLMService",
    "LLMProvider",
    "llm_router",
    "ChatMessage",
    "CompletionRequest",
    "CompletionResponse",
    "ProfileAnalysisRequest",
    "JobAnalysisRequest",
    "LLMHealthResponse",
    "SkillAnalysis",
    "JobRequirements"
]