"""
XAI Pipeline for Talent-Job Matching Explanation

Two-stage explanation generation:
- Stage 1: Field-level XAI analysis (6 fields)
- Stage 2: UI-level category aggregation (3 categories)
"""

from typing import List, Literal
from ai.matching.xai_models import (
    Stage1FieldResult,
    Stage2CategoryResult,
)


# ==================== Stage 1: Field-level Analysis ====================

def run_stage1_field_analysis(
    field: Literal["roles", "skills", "growth", "career", "vision", "culture"],
    talent_field_summary: str,
    job_field_summary: str,
    similarity_score: float
) -> Stage1FieldResult:
    """
    Stage 1: Generate field-level XAI explanation
    
    Analyzes a single field (e.g., "roles") and produces:
    - matching_reason: Why talent and job match in this field
    - risk_or_gap: Potential concerns or gaps
    - suggested_questions: Questions to validate the match
    
    Args:
        field: Field name (roles, skills, growth, career, vision, culture)
        talent_field_summary: Talent's field summary (500-700 chars)
        job_field_summary: Job's field summary (500-700 chars)
        similarity_score: Cosine similarity score (0.0-1.0)
    
    Returns:
        Stage1FieldResult with XAI explanation
    """
    # TODO: Build LLM prompt
    prompt = _build_stage1_prompt(
        field=field,
        talent_summary=talent_field_summary,
        job_summary=job_field_summary,
        score=similarity_score
    )
    
    # TODO: Call LLM (placeholder)
    llm_response = _call_llm_stage1(prompt)
    
    # TODO: Parse LLM response into structured output
    result = _parse_stage1_response(field, llm_response)
    
    return result


def _build_stage1_prompt(
    field: str,
    talent_summary: str,
    job_summary: str,
    score: float
) -> str:
    """Build LLM prompt for Stage 1 field analysis"""
    
    # Placeholder prompt template
    prompt = f"""
You are an expert HR analyst specializing in talent-job matching.

Field: {field}
Similarity Score: {score:.3f}

Talent Summary:
{talent_summary}

Job Summary:
{job_summary}

Analyze this field and provide:
1. matching_reason: Why talent and job match in this field
2. risk_or_gap: Potential risks or gaps
3. suggested_questions: 2-3 questions to validate this match

Return JSON format:
{{
  "field": "{field}",
  "matching_reason": "...",
  "risk_or_gap": "...",
  "suggested_questions": ["...", "..."]
}}
"""
    return prompt


def _call_llm_stage1(prompt: str) -> dict:
    """Call LLM for Stage 1 analysis (placeholder)"""
    
    # TODO: Integrate actual LLM call (OpenAI, Anthropic, etc.)
    # For now, return mock response
    mock_response = {
        "field": "roles",
        "matching_reason": "Both require strong technical leadership and system design capabilities.",
        "risk_or_gap": "Job requires more hands-on coding experience than talent currently has.",
        "suggested_questions": [
            "Can you describe a recent system architecture you designed?",
            "How do you balance technical work with team management?"
        ]
    }
    return mock_response


def _parse_stage1_response(field: str, llm_response: dict) -> Stage1FieldResult:
    """Parse LLM response into Stage1FieldResult"""
    
    # Validate and construct Pydantic model
    result = Stage1FieldResult(
        field=field,
        matching_reason=llm_response.get("matching_reason", ""),
        risk_or_gap=llm_response.get("risk_or_gap", ""),
        suggested_questions=llm_response.get("suggested_questions", [])
    )
    return result


# ==================== Stage 2: Category Aggregation ====================

def run_stage2_category_aggregation(
    category: Literal["직무 적합성", "성장 가능성", "문화 적합성"],
    field_results: List[Stage1FieldResult]
) -> Stage2CategoryResult:
    """
    Stage 2: Aggregate field results into UI-level category explanation
    
    Combines multiple Stage 1 field results (e.g., roles + skills)
    into a single category-level explanation for the UI.
    
    Args:
        category: UI category name (직무 적합성, 성장 가능성, 문화 적합성)
        field_results: List of Stage1FieldResult objects to aggregate
    
    Returns:
        Stage2CategoryResult with aggregated explanation
    """
    # TODO: Build LLM prompt for aggregation
    prompt = _build_stage2_prompt(category, field_results)
    
    # TODO: Call LLM (placeholder)
    llm_response = _call_llm_stage2(prompt)
    
    # TODO: Parse LLM response into structured output
    result = _parse_stage2_response(category, llm_response)
    
    return result


def _build_stage2_prompt(
    category: str,
    field_results: List[Stage1FieldResult]
) -> str:
    """Build LLM prompt for Stage 2 category aggregation"""
    
    # Combine field results into context
    field_context = "\n\n".join([
        f"Field: {fr.field}\n"
        f"Matching Reason: {fr.matching_reason}\n"
        f"Risk/Gap: {fr.risk_or_gap}\n"
        f"Questions: {', '.join(fr.suggested_questions)}"
        for fr in field_results
    ])
    
    # Placeholder prompt template
    prompt = f"""
You are an expert HR analyst. Aggregate the following field-level analyses
into a single UI-level category explanation.

Category: {category}

Field-level Analysis Results:
{field_context}

Provide:
1. matching_evidence: Overall evidence why this category matches
2. check_points: Key points to check or consider
3. suggested_questions: 3-5 aggregated questions for this category

Return JSON format:
{{
  "category": "{category}",
  "matching_evidence": "...",
  "check_points": "...",
  "suggested_questions": ["...", "...", "..."]
}}
"""
    return prompt


def _call_llm_stage2(prompt: str) -> dict:
    """Call LLM for Stage 2 aggregation (placeholder)"""
    
    # TODO: Integrate actual LLM call
    # For now, return mock response
    mock_response = {
        "category": "직무 적합성",
        "matching_evidence": "Strong technical background and leadership experience align well with job requirements.",
        "check_points": "Verify hands-on coding experience and system design capabilities through practical examples.",
        "suggested_questions": [
            "Can you describe a recent system architecture you designed?",
            "How do you balance technical work with team management?",
            "What's your approach to code reviews and technical mentoring?"
        ]
    }
    return mock_response


def _parse_stage2_response(category: str, llm_response: dict) -> Stage2CategoryResult:
    """Parse LLM response into Stage2CategoryResult"""
    
    # Validate and construct Pydantic model
    result = Stage2CategoryResult(
        category=category,
        matching_evidence=llm_response.get("matching_evidence", ""),
        check_points=llm_response.get("check_points", ""),
        suggested_questions=llm_response.get("suggested_questions", [])
    )
    return result


# ==================== Helper Functions ====================

def get_category_fields(category: str) -> List[str]:
    """Get field names for a given UI category"""
    
    category_mapping = {
        "직무 적합성": ["roles", "skills"],
        "성장 가능성": ["growth", "career", "vision"],
        "문화 적합성": ["culture"]
    }
    return category_mapping.get(category, [])


def validate_field_results(
    category: str,
    field_results: List[Stage1FieldResult]
) -> bool:
    """Validate that field_results match the expected fields for the category"""
    
    expected_fields = set(get_category_fields(category))
    actual_fields = {fr.field for fr in field_results}
    
    return expected_fields == actual_fields
