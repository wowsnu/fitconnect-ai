"""
Pydantic models for AI Interview module
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class InterviewType(str, Enum):
    """Types of AI interviews"""
    CANDIDATE_COMPETENCY = "candidate_competency"
    JOB_REQUIREMENT = "job_requirement"
    GENERAL = "general"


class InterviewPhase(str, Enum):
    """Interview phases"""
    INTRODUCTION = "introduction"
    MAIN_QUESTIONS = "main_questions"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"
    COMPLETED = "completed"


class StartInterviewRequest(BaseModel):
    """Request model to start an interview"""
    participant_id: str = Field(..., description="ID of the participant")
    interview_type: InterviewType = Field(..., description="Type of interview")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class InterviewSessionResponse(BaseModel):
    """Response model for interview session"""
    session_id: str = Field(..., description="Interview session ID")
    interview_type: InterviewType = Field(..., description="Type of interview")
    current_phase: InterviewPhase = Field(..., description="Current interview phase")
    participant_id: str = Field(..., description="Participant ID")
    created_at: datetime = Field(..., description="Session creation time")
    first_question: Optional[str] = Field(None, description="First question")


class NextQuestionResponse(BaseModel):
    """Response model for next question"""
    question: Optional[str] = Field(None, description="Next interview question")
    question_id: str = Field(..., description="Question ID")
    phase: InterviewPhase = Field(..., description="Current phase")
    is_completed: bool = Field(False, description="Whether interview is completed")


class AudioResponseRequest(BaseModel):
    """Request model for processing audio response"""
    session_id: str = Field(..., description="Interview session ID")
    question_id: Optional[str] = Field(None, description="Question ID (optional)")


class ProcessedResponse(BaseModel):
    """Model for processed interview response"""
    response_id: str = Field(..., description="Response ID")
    question_id: Optional[str] = Field(None, description="Related question ID")
    transcription: str = Field(..., description="Transcribed text")
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    confidence_score: float = Field(..., description="Transcription confidence")
    timestamp: datetime = Field(..., description="Response timestamp")


class ResponseAnalysisResponse(BaseModel):
    """Response model for audio processing"""
    transcription: str = Field(..., description="Transcribed text")
    analysis: Dict[str, Any] = Field(..., description="Response analysis")
    metadata: Dict[str, Any] = Field(..., description="STT metadata")
    next_question: Optional[str] = Field(None, description="Auto-generated next question")


class FollowUpQuestionRequest(BaseModel):
    """Request model for generating follow-up questions"""
    session_id: str = Field(..., description="Interview session ID")
    context: Optional[str] = Field(None, description="Additional context")


class InterviewQuestion(BaseModel):
    """Model for interview questions"""
    question_id: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    phase: str = Field(..., description="Interview phase")
    asked_at: datetime = Field(..., description="When question was asked")
    question_type: str = Field("template", description="Question type (template/ai_generated)")


class InterviewResponse(BaseModel):
    """Model for interview responses"""
    response_id: str = Field(..., description="Response ID")
    question_id: Optional[str] = Field(None, description="Related question ID")
    transcription: str = Field(..., description="Transcribed response")
    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    responded_at: datetime = Field(..., description="When response was given")
    phase: str = Field(..., description="Interview phase")


class SessionSummary(BaseModel):
    """Model for interview session summary"""
    session_id: str = Field(..., description="Session ID")
    interview_type: InterviewType = Field(..., description="Interview type")
    current_phase: InterviewPhase = Field(..., description="Current phase")
    questions_count: int = Field(..., description="Number of questions asked")
    responses_count: int = Field(..., description="Number of responses received")
    duration_minutes: float = Field(..., description="Interview duration in minutes")
    created_at: datetime = Field(..., description="Session start time")
    updated_at: datetime = Field(..., description="Last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")


class DetailedSessionSummary(SessionSummary):
    """Detailed session summary with questions and responses"""
    questions: List[InterviewQuestion] = Field(default_factory=list, description="All questions")
    responses: List[InterviewResponse] = Field(default_factory=list, description="All responses")


class InterviewAnalytics(BaseModel):
    """Model for interview analytics"""
    session_id: str = Field(..., description="Session ID")
    overall_score: float = Field(..., description="Overall interview score")
    competency_scores: Dict[str, float] = Field(..., description="Scores by competency")
    key_strengths: List[str] = Field(default_factory=list, description="Identified strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas for improvement")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class CompletionReport(BaseModel):
    """Model for interview completion report"""
    session_summary: SessionSummary = Field(..., description="Session summary")
    analytics: Optional[InterviewAnalytics] = Field(None, description="Interview analytics")
    transcript: List[Dict[str, str]] = Field(default_factory=list, description="Full conversation transcript")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next steps")


class InterviewHealthResponse(BaseModel):
    """Health check response for interview service"""
    service_status: str = Field(..., description="Service status")
    active_sessions: int = Field(..., description="Number of active sessions")
    dependencies: Dict[str, bool] = Field(..., description="Dependency status")
    templates_loaded: bool = Field(..., description="Whether templates are loaded")