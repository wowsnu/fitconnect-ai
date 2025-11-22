"""
XAI (Explainable AI) Pydantic Models for Talent-Job Matching

Two-stage explanation generation:
- Stage 1: Field-level XAI (6 fields)
- Stage 2: UI-level aggregation (3 categories)
"""

from typing import List, Literal
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
    """Request for generating match explanation (minimal form)"""
    
    talent_user_id: int = Field(
        ...,
        description="Talent user ID"
    )
    job_posting_id: int = Field(
        ...,
        description="Job posting ID"
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
