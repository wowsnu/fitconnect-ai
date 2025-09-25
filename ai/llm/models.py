"""
Pydantic models for LLM module
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class CompletionRequest(BaseModel):
    """Request model for LLM completion"""
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    provider: LLMProvider = Field(LLMProvider.OPENAI, description="LLM provider")
    model: Optional[str] = Field(None, description="Model name (provider-specific)")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(1000, ge=1, le=4000, description="Maximum tokens to generate")


class CompletionResponse(BaseModel):
    """Response model for LLM completion"""
    content: str = Field(..., description="Generated content")
    provider: LLMProvider = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model used")
    usage: Dict[str, Any] = Field(..., description="Token usage information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProfileAnalysisRequest(BaseModel):
    """Request model for candidate profile analysis"""
    profile_text: str = Field(..., description="Candidate profile text to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis to perform")


class JobAnalysisRequest(BaseModel):
    """Request model for job posting analysis"""
    job_posting_text: str = Field(..., description="Job posting text to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis to perform")


class SkillAnalysis(BaseModel):
    """Model for skill analysis results"""
    technical_skills: List[str] = Field(default_factory=list, description="Technical skills")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills")
    experience_level: str = Field("", description="Experience level")
    strengths: List[str] = Field(default_factory=list, description="Key strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas for improvement")


class ProfileAnalysisResponse(BaseModel):
    """Response model for profile analysis"""
    analysis: Dict[str, Any] = Field(..., description="Structured analysis results")
    skills: SkillAnalysis = Field(..., description="Extracted skills information")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Analysis confidence score")


class JobRequirements(BaseModel):
    """Model for job requirements"""
    required_skills: List[str] = Field(default_factory=list, description="Required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")
    experience_requirements: str = Field("", description="Experience requirements")
    education_requirements: str = Field("", description="Education requirements")
    soft_skills: List[str] = Field(default_factory=list, description="Required soft skills")


class JobAnalysisResponse(BaseModel):
    """Response model for job posting analysis"""
    analysis: Dict[str, Any] = Field(..., description="Structured analysis results")
    requirements: JobRequirements = Field(..., description="Extracted job requirements")
    company_culture: List[str] = Field(default_factory=list, description="Company culture aspects")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Analysis confidence score")


class LLMHealthResponse(BaseModel):
    """Health check response for LLM service"""
    service_status: str = Field(..., description="Overall service status")
    providers: Dict[str, bool] = Field(..., description="Provider availability")
    available_models: Dict[str, List[str]] = Field(default_factory=dict, description="Available models per provider")


class InterviewQuestion(BaseModel):
    """Model for generated interview questions"""
    question: str = Field(..., description="Interview question")
    category: str = Field(..., description="Question category (technical, behavioral, etc.)")
    difficulty: str = Field(..., description="Question difficulty level")
    purpose: str = Field(..., description="Purpose of the question")


class InterviewQuestionsRequest(BaseModel):
    """Request model for interview question generation"""
    job_requirements: JobRequirements = Field(..., description="Job requirements")
    candidate_profile: Optional[SkillAnalysis] = Field(None, description="Candidate profile (optional)")
    question_count: int = Field(5, ge=1, le=20, description="Number of questions to generate")
    focus_areas: List[str] = Field(default_factory=list, description="Specific areas to focus on")


class InterviewQuestionsResponse(BaseModel):
    """Response model for interview question generation"""
    questions: List[InterviewQuestion] = Field(..., description="Generated interview questions")
    total_count: int = Field(..., description="Total number of questions generated")
    categories: Dict[str, int] = Field(..., description="Question count per category")