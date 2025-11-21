"""
XAI (Explainable AI) Match Explanation API Routes

Provides endpoints for generating talent-job match explanations
using LangGraph pipeline (summary-based, no RAG).
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ai.matching.xai_models import (
    MatchExplainRequest,
    Stage2CategoryResult
)
from ai.matching.xai_cache import (
    compute_request_hash,
    get_cached_response,
    upsert_cached_response
)
from ai.matching.xai_graph import generate_match_explanation


# Router setup
xai_router = APIRouter(prefix="/match", tags=["XAI"])
logger = logging.getLogger(__name__)


# ==================== Response Models ====================

class MatchExplainResponse(BaseModel):
    """Response for match explanation endpoint"""
    
    job_fit: Dict[str, Any]
    growth_potential: Dict[str, Any]
    culture_fit: Dict[str, Any]
    metadata: Dict[str, Any]


# ==================== Placeholder Data Loaders ====================

def get_talent_summaries(request: MatchExplainRequest) -> Dict[str, str]:
    """
    Load talent field summaries from request
    
    TODO: Replace with actual database/service call
    
    Args:
        request: MatchExplainRequest with talent_summaries
    
    Returns:
        Dict mapping field names to summaries
    """
    summaries = {}
    for field_summary in request.talent_summaries:
        summaries[field_summary.field] = field_summary.summary
    
    # Validate all 6 fields present
    expected_fields = {"roles", "skills", "growth", "career", "vision", "culture"}
    actual_fields = set(summaries.keys())
    
    if actual_fields != expected_fields:
        missing = expected_fields - actual_fields
        extra = actual_fields - expected_fields
        raise ValueError(
            f"Invalid talent summaries. Missing: {missing}, Extra: {extra}"
        )
    
    logger.info(f"Loaded talent summaries for fields: {list(summaries.keys())}")
    return summaries


def get_job_summaries(request: MatchExplainRequest) -> Dict[str, str]:
    """
    Load job field summaries from request
    
    TODO: Replace with actual database/service call
    
    Args:
        request: MatchExplainRequest with job_summaries
    
    Returns:
        Dict mapping field names to summaries
    """
    summaries = {}
    for field_summary in request.job_summaries:
        summaries[field_summary.field] = field_summary.summary
    
    # Validate all 6 fields present
    expected_fields = {"roles", "skills", "growth", "career", "vision", "culture"}
    actual_fields = set(summaries.keys())
    
    if actual_fields != expected_fields:
        missing = expected_fields - actual_fields
        extra = actual_fields - expected_fields
        raise ValueError(
            f"Invalid job summaries. Missing: {missing}, Extra: {extra}"
        )
    
    logger.info(f"Loaded job summaries for fields: {list(summaries.keys())}")
    return summaries


def get_similarity_scores(request: MatchExplainRequest) -> Dict[str, float]:
    """
    Load field similarity scores from request
    
    TODO: Replace with actual similarity computation service
    
    Args:
        request: MatchExplainRequest with similarity_scores
    
    Returns:
        Dict mapping field names to cosine similarity scores
    """
    scores = request.field_similarity_scores
    
    # Validate all 6 fields present
    expected_fields = {"roles", "skills", "growth", "career", "vision", "culture"}
    actual_fields = set(scores.keys())
    
    if actual_fields != expected_fields:
        missing = expected_fields - actual_fields
        extra = actual_fields - expected_fields
        raise ValueError(
            f"Invalid similarity scores. Missing: {missing}, Extra: {extra}"
        )
    
    # Validate score ranges
    for field, score in scores.items():
        if not (0.0 <= score <= 1.0):
            raise ValueError(
                f"Invalid similarity score for field '{field}': {score} "
                f"(must be between 0.0 and 1.0)"
            )
    
    logger.info(f"Loaded similarity scores: {scores}")
    return scores


def validate_request(request: MatchExplainRequest) -> None:
    """
    Validate match explain request
    
    Args:
        request: MatchExplainRequest to validate
    
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Validate field counts
        if len(request.talent_summaries) != 6:
            raise ValueError(
                f"Expected 6 talent summaries, got {len(request.talent_summaries)}"
            )
        
        if len(request.job_summaries) != 6:
            raise ValueError(
                f"Expected 6 job summaries, got {len(request.job_summaries)}"
            )
        
        if len(request.field_similarity_scores) != 6:
            raise ValueError(
                f"Expected 6 similarity scores, got {len(request.field_similarity_scores)}"
            )
        
        # Validate field names consistency
        talent_fields = {fs.field for fs in request.talent_summaries}
        job_fields = {fs.field for fs in request.job_summaries}
        score_fields = set(request.field_similarity_scores.keys())
        
        if talent_fields != job_fields or talent_fields != score_fields:
            raise ValueError(
                f"Field mismatch. Talent: {talent_fields}, "
                f"Job: {job_fields}, Scores: {score_fields}"
            )
        
        # (요약 길이 검증 제거) summary는 아무 길이도 허용
        
        logger.info("Request validation passed")
        
    except ValueError as e:
        logger.error(f"Request validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== API Endpoint ====================

@xai_router.post("/explain", response_model=MatchExplainResponse)
async def explain_match(request: MatchExplainRequest) -> MatchExplainResponse:
    """
    Generate XAI explanation for talent-job match
    
    This endpoint orchestrates a two-stage XAI generation pipeline:
    1. Stage 1: Field-level analysis (6 fields using summaries + similarity scores)
    2. Stage 2: Category-level aggregation (3 UI categories)
    
    Args:
        request: MatchExplainRequest containing:
            - talent_summaries: 6 field summaries (500-700 chars each)
            - job_summaries: 6 field summaries (500-700 chars each)
            - field_similarity_scores: 6 cosine similarity scores
    
    Returns:
        MatchExplainResponse with 3 category explanations:
            - job_fit (직무 적합성): roles + skills
            - growth_potential (성장 가능성): growth + career + vision
            - culture_fit (문화 적합성): culture
    
    Raises:
        HTTPException: If validation fails or pipeline execution fails
    """
    logger.info(
        f"[XAI] Received match explanation request with "
        f"{len(request.talent_summaries)} talent summaries, "
        f"{len(request.job_summaries)} job summaries"
    )
    
    import json
    import os
    from datetime import datetime
    try:
        # Step 1: Validate request
        validate_request(request)

        # Step 1.5: Cache lookup (if identifiers provided)
        cache_talent_id = request.talent_user_id or request.talent_id
        cache_jd_id = request.job_posting_id or request.jd_id
        cache_enabled = cache_talent_id is not None and cache_jd_id is not None
        cached_response = None
        request_hash = None
        if cache_enabled:
            request_hash = compute_request_hash(request.dict())
            cached_response = get_cached_response(
                talent_id=cache_talent_id,
                jd_id=cache_jd_id,
                request_hash=request_hash
            )
            if cached_response:
                logger.info(
                    f"[XAI] Cache hit for talent_id={cache_talent_id}, jd_id={cache_jd_id}"
                )
                return MatchExplainResponse(**cached_response)
            logger.info(
                f"[XAI] Cache miss for talent_id={cache_talent_id}, jd_id={cache_jd_id}"
            )
        
        # Step 2: Load summaries
        talent_summaries = get_talent_summaries(request)
        job_summaries = get_job_summaries(request)
        
        # Step 3: Load similarity scores
        similarity_scores = get_similarity_scores(request)
        
        logger.info(
            f"[XAI] Starting XAI pipeline with {len(talent_summaries)} fields"
        )
        
        # Step 4: Execute LangGraph pipeline
        final_explanation = generate_match_explanation(
            talent_summaries=talent_summaries,
            job_summaries=job_summaries,
            similarity_scores=similarity_scores
        )
        
        logger.info("[XAI] Pipeline execution completed successfully")
        
        # Step 5: Format response
        response = MatchExplainResponse(
            job_fit=final_explanation.get("직무 적합성", {}),
            growth_potential=final_explanation.get("성장 가능성", {}),
            culture_fit=final_explanation.get("문화 적합성", {}),
            metadata=final_explanation.get("metadata", {})
        )
        
        logger.info(
            f"[XAI] Response prepared with categories: "
            f"job_fit={bool(response.job_fit)}, "
            f"growth_potential={bool(response.growth_potential)}, "
            f"culture_fit={bool(response.culture_fit)}"
        )

        # Step 5.5: Save cache (best-effort)
        try:
            if cache_enabled and request_hash:
                upsert_cached_response(
                    talent_id=cache_talent_id,
                    jd_id=cache_jd_id,
                    request_hash=request_hash,
                    response=response.dict()
                )
                logger.info(
                    f"[XAI] Cached response for talent_id={cache_talent_id}, jd_id={cache_jd_id}"
                )
        except Exception as cache_error:
            logger.warning(f"[XAI] Failed to cache response: {cache_error}")

        # Step 6: Save request/response to file (simple example)
        save_dir = "xai_logs"
        os.makedirs(save_dir, exist_ok=True)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(save_dir, f"xai_{now}.json"), "w", encoding="utf-8") as f:
            json.dump({
                "request": request.dict(),
                "response": response.dict()
            }, f, ensure_ascii=False, indent=2)
        return response
        
    except ValueError as e:
        logger.error(f"[XAI] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    
    except Exception as e:
        logger.exception(f"[XAI] Pipeline execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate match explanation: {str(e)}"
        )


# ==================== Health Check ====================

@xai_router.get("/health")
async def xai_health_check() -> Dict[str, str]:
    """
    Health check endpoint for XAI service
    
    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "xai-match-explanation",
        "version": "1.0.0"
    }


# ==================== Debug/Testing Endpoints ====================

@xai_router.post("/explain/mock")
async def explain_match_mock() -> MatchExplainResponse:
    """
    Mock endpoint for testing with sample data
    
    Returns:
        Sample match explanation response
    """
    logger.info("[XAI] Mock endpoint called")
    
    # Create mock request with sample data
    from ai.matching.xai_models import FieldSummary
    
    mock_request = MatchExplainRequest(
        talent_summaries=[
            FieldSummary(
                field="roles",
                summary="Software engineer with 5 years of experience in backend development, specializing in microservices architecture and API design. Led multiple projects involving RESTful API development and database optimization. Strong background in Python and Node.js with experience in cloud platforms like AWS and GCP. Proven track record of delivering scalable solutions for high-traffic applications. Interested in technical leadership roles that combine hands-on coding with system architecture design."
            ),
            FieldSummary(
                field="skills",
                summary="Technical skills include Python, Java, Node.js, Docker, Kubernetes, PostgreSQL, MongoDB, Redis, AWS (EC2, S3, Lambda), and CI/CD pipelines. Proficient in designing RESTful APIs, implementing microservices, and optimizing database queries. Experience with agile methodologies, code reviews, and technical documentation. Soft skills include team collaboration, mentoring junior developers, and effective communication with stakeholders across technical and non-technical teams."
            ),
            FieldSummary(
                field="growth",
                summary="Seeking opportunities to grow into a senior technical leadership role, focusing on system architecture and technical strategy. Interested in learning more about distributed systems, cloud-native technologies, and DevOps practices. Currently pursuing cloud certifications and studying advanced system design patterns. Eager to contribute to open-source projects and share knowledge through tech blogs and conference talks. Looking for a role that offers mentorship opportunities and exposure to cutting-edge technologies."
            ),
            FieldSummary(
                field="career",
                summary="Career progression from junior developer to senior engineer over 5 years, consistently taking on more complex projects and technical challenges. Previously worked at a startup where gained broad experience across the full stack. Transitioned to a larger company to deepen expertise in backend systems and learn enterprise-scale architecture. Achievements include reducing API latency by 40%, implementing automated testing that caught 95% of bugs pre-production, and mentoring 3 junior developers who were promoted within a year."
            ),
            FieldSummary(
                field="vision",
                summary="Vision is to become a technical architect who can bridge the gap between business needs and technical solutions. Passionate about building systems that are not only technically sound but also deliver real value to users. Believes in continuous learning and knowledge sharing as key to professional growth. Long-term goal is to contribute to the tech community through open-source projects, technical writing, and mentoring the next generation of engineers. Values innovation, collaboration, and a culture of excellence."
            ),
            FieldSummary(
                field="culture",
                summary="Thrives in collaborative environments with strong engineering culture and emphasis on code quality. Prefers flat hierarchies where ideas are valued over titles. Appreciates companies that invest in employee growth through training, conferences, and learning budgets. Values work-life balance and flexible working arrangements. Seeks a culture of transparency, open communication, and psychological safety where team members can share ideas and learn from failures. Believes in the importance of diversity and inclusion in building better products."
            )
        ],
        job_summaries=[
            FieldSummary(
                field="roles",
                summary="Senior Backend Engineer role responsible for designing and implementing scalable microservices for our e-commerce platform. Will lead technical initiatives, mentor junior engineers, and collaborate with product managers to translate business requirements into technical solutions. Expected to drive architectural decisions, establish coding standards, and ensure system reliability. Must have strong experience in backend development, API design, and distributed systems. This role combines hands-on development (70%) with technical leadership (30%)."
            ),
            FieldSummary(
                field="skills",
                summary="Required skills: 5+ years of backend development experience with Python or Java, strong understanding of microservices architecture, RESTful API design, and database management (SQL and NoSQL). Must be proficient with cloud platforms (AWS preferred), containerization (Docker, Kubernetes), and CI/CD pipelines. Experience with high-traffic systems, performance optimization, and monitoring tools. Strong communication skills for collaborating with cross-functional teams and technical documentation."
            ),
            FieldSummary(
                field="growth",
                summary="This role offers clear growth path to Principal Engineer or Engineering Manager positions. We provide annual learning budgets for conferences, courses, and certifications. Engineers are encouraged to dedicate 10% of their time to learning and innovation projects. Opportunities to work on cutting-edge technologies including cloud-native architectures, serverless computing, and event-driven systems. Regular tech talks, internal workshops, and mentorship programs to support continuous professional development."
            ),
            FieldSummary(
                field="career",
                summary="We're looking for someone who has demonstrated consistent career growth and increasing technical responsibility. Ideal candidate has progressed from individual contributor to taking on more complex projects and mentoring responsibilities. Track record of delivering high-quality, scalable solutions and driving technical excellence. Ability to balance hands-on coding with strategic thinking and technical leadership. Previous experience in fast-paced, agile environments with a focus on continuous delivery and iterative development."
            ),
            FieldSummary(
                field="vision",
                summary="Join a company that's building the next generation of e-commerce technology. We're reimagining how millions of people shop online by creating seamless, personalized experiences powered by cutting-edge technology. Our technical vision focuses on scalability, reliability, and innovation. We value engineers who think beyond code to understand user impact and business value. Looking for team members who are passionate about technical excellence and excited to shape the future of online retail through technology."
            ),
            FieldSummary(
                field="culture",
                summary="We foster a culture of collaboration, innovation, and continuous improvement. Our engineering teams follow agile practices with emphasis on code quality, peer reviews, and knowledge sharing. We believe in flat organizational structure where the best ideas win regardless of seniority. Strong focus on work-life balance with flexible hours and remote work options. Regular team events, hackathons, and social activities to build community. We're committed to diversity, equity, and inclusion, creating an environment where everyone can thrive and do their best work."
            )
        ],
        field_similarity_scores={
            "roles": 0.92,
            "skills": 0.89,
            "growth": 0.87,
            "career": 0.91,
            "vision": 0.85,
            "culture": 0.88
        }
    )
    
    # Use the actual pipeline with mock data
    return await explain_match(mock_request)
