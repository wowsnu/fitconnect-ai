"""
XAI (Explainable AI) Pydantic Models for Talent-Job Matching

Two-stage explanation generation:
- Stage 1: Field-level XAI (6 fields)
- Stage 2: UI-level aggregation (3 categories)
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ==================== Field Summary ====================

class FieldSummary(BaseModel):
    """Single field summary for Talent or Job"""
    
    field: Literal["roles", "skills", "growth", "career", "vision", "culture"] = Field(
        ...,
        description="Field name"
    )
    summary: str = Field(
        ...,
        description="Field summary text (any length)"
    )


# ==================== Stage 1: Field-level XAI ====================

class Stage1FieldInput(BaseModel):
    """Input for Stage 1 field-level XAI generation"""
    
    field: Literal["roles", "skills", "growth", "career", "vision", "culture"] = Field(
        ...,
        description="Field name"
    )
    talent_field_summary: str = Field(
        ...,
        description="Talent field summary (any length)"
    )
    job_field_summary: str = Field(
        ...,
        description="Job field summary (any length)"
    )
    field_similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score for this field"
    )


class Stage1FieldResult(BaseModel):
    """Output for Stage 1 field-level XAI"""
    
    field: Literal["roles", "skills", "growth", "career", "vision", "culture"] = Field(
        ...,
        description="Field name"
    )
    matching_reason: str = Field(
        ...,
        description="Why this field matches between talent and job"
    )
    risk_or_gap: str = Field(
        ...,
        description="Potential risks or gaps identified in this field"
    )
    suggested_questions: List[str] = Field(
        ...,
        min_items=1,
        max_items=3,
        description="Suggested questions to validate this match (1-3 questions)"
    )


# ==================== Stage 2: UI-level Aggregation ====================

class Stage2CategoryInput(BaseModel):
    """Input for Stage 2 category-level aggregation"""
    
    category: Literal["직무 적합성", "성장 가능성", "문화 적합성"] = Field(
        ...,
        description="UI category name"
    )
    field_results: List[Stage1FieldResult] = Field(
        ...,
        min_items=1,
        description="Stage 1 field results to aggregate"
    )


class Stage2CategoryResult(BaseModel):
    """Output for Stage 2 category-level aggregation"""
    
    category: Literal["직무 적합성", "성장 가능성", "문화 적합성"] = Field(
        ...,
        description="UI category name"
    )
    matching_evidence: str = Field(
        ...,
        description="Evidence and reasons why this category matches"
    )
    check_points: str = Field(
        ...,
        description="Important points to check or consider for this category"
    )
    suggested_questions: List[str] = Field(
        ...,
        min_items=1,
        max_items=5,
        description="Aggregated suggested questions for this category (1-5 questions)"
    )


# ==================== API Request/Response ====================

class MatchExplainRequest(BaseModel):
    """Request for generating match explanation"""
    
    talent_id: Optional[int] = Field(
        None,
        description="Talent user ID (for caching)"
    )
    talent_user_id: Optional[int] = Field(
        None,
        description="Alias of talent_id (external naming)"
    )
    jd_id: Optional[int] = Field(
        None,
        description="Job description ID (for caching)"
    )
    job_posting_id: Optional[int] = Field(
        None,
        description="Alias of jd_id (external naming)"
    )
    talent_summaries: List[FieldSummary] = Field(
        ...,
        min_items=6,
        max_items=6,
        description="Talent field summaries (must contain all 6 fields)"
    )
    job_summaries: List[FieldSummary] = Field(
        ...,
        min_items=6,
        max_items=6,
        description="Job field summaries (must contain all 6 fields)"
    )
    field_similarity_scores: dict[str, float] = Field(
        ...,
        description="Cosine similarity scores per field (keys: roles, skills, growth, career, vision, culture)"
    )


class MatchExplainResponse(BaseModel):
    """Response for match explanation"""
    
    stage1_results: List[Stage1FieldResult] = Field(
        ...,
        min_items=6,
        max_items=6,
        description="Stage 1 field-level XAI results (6 fields)"
    )
    stage2_results: List[Stage2CategoryResult] = Field(
        ...,
        min_items=3,
        max_items=3,
        description="Stage 2 category-level aggregation results (3 categories)"
    )
