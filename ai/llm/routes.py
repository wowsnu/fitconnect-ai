"""
FastAPI routes for LLM functionality
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .service import llm_service
from .models import (
    CompletionRequest,
    CompletionResponse,
    ProfileAnalysisRequest,
    ProfileAnalysisResponse,
    JobAnalysisRequest,
    JobAnalysisResponse,
    LLMHealthResponse,
    InterviewQuestionsRequest,
    InterviewQuestionsResponse,
    SkillAnalysis,
    JobRequirements,
    InterviewQuestion
)

logger = logging.getLogger(__name__)

llm_router = APIRouter()


@llm_router.post("/completion", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):
    """
    Generate text completion using specified LLM provider

    - **messages**: List of chat messages
    - **provider**: LLM provider (openai, anthropic)
    - **model**: Model name (optional, uses default)
    - **temperature**: Sampling temperature (0.0 to 2.0)
    - **max_tokens**: Maximum tokens to generate
    """
    try:
        response = await llm_service.generate_completion(
            messages=request.messages,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return response

    except ValueError as e:
        logger.error(f"LLM completion error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LLM completion unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@llm_router.post("/analyze/profile", response_model=Dict[str, Any])
async def analyze_candidate_profile(request: ProfileAnalysisRequest):
    """
    Analyze candidate profile and extract key competencies

    - **profile_text**: Candidate profile text (resume, interview transcript, etc.)
    - **analysis_type**: Type of analysis to perform
    """
    try:
        analysis = await llm_service.analyze_candidate_profile(request.profile_text)

        # Extract skills information for structured response
        skills = SkillAnalysis()
        if isinstance(analysis, dict):
            skills.technical_skills = analysis.get("technical_skills", [])
            skills.soft_skills = analysis.get("soft_skills", [])
            skills.experience_level = analysis.get("experience_level", "")
            skills.strengths = analysis.get("strengths", [])
            skills.areas_for_improvement = analysis.get("areas_for_improvement", [])

        return {
            "analysis": analysis,
            "skills": skills.dict(),
            "confidence_score": 0.85  # Placeholder confidence score
        }

    except ValueError as e:
        logger.error(f"Profile analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Profile analysis unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@llm_router.post("/analyze/job", response_model=Dict[str, Any])
async def analyze_job_posting(request: JobAnalysisRequest):
    """
    Analyze job posting and extract requirements

    - **job_posting_text**: Job posting description
    - **analysis_type**: Type of analysis to perform
    """
    try:
        analysis = await llm_service.analyze_job_posting(request.job_posting_text)

        # Extract requirements information for structured response
        requirements = JobRequirements()
        if isinstance(analysis, dict):
            requirements.required_skills = analysis.get("required_skills", [])
            requirements.preferred_skills = analysis.get("preferred_skills", [])
            requirements.experience_requirements = analysis.get("experience_requirements", "")
            requirements.education_requirements = analysis.get("education_requirements", "")
            requirements.soft_skills = analysis.get("soft_skills", [])

        return {
            "analysis": analysis,
            "requirements": requirements.dict(),
            "company_culture": analysis.get("company_culture", []) if isinstance(analysis, dict) else [],
            "confidence_score": 0.85  # Placeholder confidence score
        }

    except ValueError as e:
        logger.error(f"Job analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Job analysis unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@llm_router.post("/interview/questions", response_model=Dict[str, Any])
async def generate_interview_questions(request: InterviewQuestionsRequest):
    """
    Generate interview questions based on job requirements and candidate profile

    - **job_requirements**: Job requirements
    - **candidate_profile**: Candidate profile (optional)
    - **question_count**: Number of questions to generate
    - **focus_areas**: Specific areas to focus on
    """
    try:
        # Create a prompt for question generation
        system_prompt = f"""
        당신은 채용 면접 전문가입니다. 주어진 채용 요구사항을 바탕으로 효과적인 면접 질문을 생성해주세요.

        요구사항:
        - 필수 기술: {', '.join(request.job_requirements.required_skills)}
        - 우대 기술: {', '.join(request.job_requirements.preferred_skills)}
        - 경력 요구사항: {request.job_requirements.experience_requirements}
        - 소프트 스킬: {', '.join(request.job_requirements.soft_skills)}

        {request.question_count}개의 면접 질문을 다음 형식으로 생성해주세요:
        각 질문마다 카테고리(기술/행동/경험), 난이도(초급/중급/고급), 목적을 명시해주세요.
        """

        from .models import ChatMessage
        messages = [ChatMessage(role="system", content=system_prompt)]

        response = await llm_service.generate_completion(
            messages=messages,
            temperature=0.8,
            max_tokens=2000
        )

        # Parse the response to extract questions (simplified for now)
        questions = []
        categories = {"technical": 0, "behavioral": 0, "experience": 0}

        # This is a simplified parser - in production, you'd want more sophisticated parsing
        lines = response.content.split('\n')
        current_question = None

        for line in lines:
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('*'):
                if current_question:
                    questions.append(current_question)

                current_question = InterviewQuestion(
                    question=line,
                    category="technical",  # Default category
                    difficulty="중급",     # Default difficulty
                    purpose="역량 평가"    # Default purpose
                )
                categories["technical"] += 1

        if current_question:
            questions.append(current_question)

        # Limit to requested count
        questions = questions[:request.question_count]

        return {
            "questions": [q.dict() for q in questions],
            "total_count": len(questions),
            "categories": categories
        }

    except Exception as e:
        logger.error(f"Interview question generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate interview questions")


@llm_router.get("/health", response_model=LLMHealthResponse)
async def llm_health_check():
    """
    Check LLM service health status
    """
    try:
        status = llm_service.health_check()

        available_models = {
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"] if status["providers"]["openai"] else [],
            "anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"] if status["providers"]["anthropic"] else []
        }

        return LLMHealthResponse(
            service_status=status["service"],
            providers=status["providers"],
            available_models=available_models
        )

    except Exception as e:
        logger.error(f"LLM health check error: {e}")
        return LLMHealthResponse(
            service_status="error",
            providers={"openai": False, "anthropic": False},
            available_models={}
        )


@llm_router.get("/")
async def llm_info():
    """
    LLM module information
    """
    return {
        "module": "Large Language Model Integration",
        "description": "LLM services for AI interviews and analysis",
        "supported_providers": ["OpenAI", "Anthropic"],
        "endpoints": {
            "POST /completion": "Generate text completion",
            "POST /analyze/profile": "Analyze candidate profile",
            "POST /analyze/job": "Analyze job posting",
            "POST /interview/questions": "Generate interview questions",
            "GET /health": "Check service health"
        }
    }