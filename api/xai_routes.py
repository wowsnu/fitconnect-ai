"""
XAI (Explainable AI) Match Explanation API Routes

Provides endpoints for generating talent-job match explanations
using LangGraph pipeline (summary-based, no RAG).
"""

import logging
from typing import Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, status
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

from ai.matching.xai_models import (
    MatchExplainRequest,
    Stage2CategoryResult
)
from ai.matching.xai_cache import (
    save_cache_to_backend,
    fetch_cache_from_backend
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


def map_compare_to_xai_inputs(compare_data: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, float]]:
    """
    Convert /api/public/matching/compare response to XAI pipeline inputs.
    """
    field_map = {
        "vector_roles": "roles",
        "vector_skills": "skills",
        "vector_growth": "growth",
        "vector_career": "career",
        "vector_vision": "vision",
        "vector_culture": "culture",
    }
    field_scores = compare_data.get("field_scores", {})

    talent_summaries: Dict[str, str] = {}
    job_summaries: Dict[str, str] = {}
    similarity_scores: Dict[str, float] = {}

    missing = []
    for key, normalized in field_map.items():
        entry = field_scores.get(key)
        if not entry:
            missing.append(key)
            continue
        similarity = entry.get("score", 0.0) / 100.0  # score is 0-100
        similarity_scores[normalized] = max(0.0, min(1.0, similarity))
        talent_summaries[normalized] = entry.get("talent_text") or ""
        job_summaries[normalized] = entry.get("job_posting_text") or ""

    if missing:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Missing field_scores keys in compare API: {missing}"
        )
    return talent_summaries, job_summaries, similarity_scores


async def fetch_compare_data(talent_user_id: int, job_posting_id: int) -> Dict[str, Any]:
    """
    Call backend compare API to retrieve vectors/scores/texts.
    """
    from config.settings import get_settings
    import httpx

    settings = get_settings()
    url = (
        f"{settings.BACKEND_API_URL.rstrip('/')}/api/public/matching/compare"
    )
    params = {
        "talent_user_id": talent_user_id,
        "job_posting_id": job_posting_id,
    }

    timeout = httpx.Timeout(connect=10.0, read=20.0, write=20.0, pool=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Talent or job posting vectors not found"
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Compare API failed: {resp.status_code} {resp.text}"
            )
        data = resp.json()
        if not data.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Compare API returned ok=false: {data}"
            )
        return data.get("data") or {}


def validate_request(request: MatchExplainRequest) -> None:
    """
    Validate match explain request
    
    Args:
        request: MatchExplainRequest to validate
    
    Raises:
        HTTPException: If validation fails
    """
    try:
        if not request.talent_user_id:
            raise ValueError("talent_user_id가 필요합니다.")
        if not request.job_posting_id:
            raise ValueError("job_posting_id가 필요합니다.")
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
    Talent-JD XAI 생성 API (최소 입력)

    필요한 입력: `talent_user_id`, `job_posting_id` 두 필드만 포함.
    - 백엔드 캐시(`/internal/xai/match-cache`)를 먼저 확인
    - 캐시 미스 시 compare API(`/api/public/matching/compare`)로 요약/점수 조회 후 LangGraph 실행
    - 실행 결과를 캐시에 저장해 이후 요청 가속
    """
    logger.info("[XAI] Received match explanation request (IDs only flow)")
    
    import json
    import os
    from datetime import datetime

    # Step 1: Validate request
    try:
        validate_request(request)
    except ValueError as e:
        logger.error(f"[XAI] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )

    cache_talent_id = request.talent_user_id
    cache_jd_id = request.job_posting_id

    # Step 2: Try backend cache (frontend도 GET 하지만 백업으로 확인)
    if cache_talent_id is not None and cache_jd_id is not None:
        cached = await fetch_cache_from_backend(cache_talent_id, cache_jd_id)
        if cached:
            return MatchExplainResponse(**cached)

    # Step 3: Fetch from compare API
    compare_data = await fetch_compare_data(
        talent_user_id=cache_talent_id,
        job_posting_id=cache_jd_id
    )
    talent_summaries, job_summaries, similarity_scores = map_compare_to_xai_inputs(compare_data)
    
    logger.info("[XAI] Starting XAI pipeline with fetched/normalized inputs")
    
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

    # Step 5.5: Save cache to backend (best-effort)
    cache_talent_id = request.talent_user_id
    cache_jd_id = request.job_posting_id
    if cache_talent_id is not None and cache_jd_id is not None:
        try:
            await save_cache_to_backend(
                talent_id=cache_talent_id,
                jd_id=cache_jd_id,
                request_json=request.dict(),
                response_json=response.dict(),
                lang="ko"
            )
        except Exception as cache_error:
            logger.warning(f"[XAI] Failed to call backend cache API: {cache_error}")

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
    
    talent_summaries = {
        "roles": "백엔드 개발 5년, 마이크로서비스/REST API 설계 경험 다수.",
        "skills": "Python, Node.js, Docker, Kubernetes, PostgreSQL, AWS 경험 풍부.",
        "growth": "시스템 아키텍트로 성장 희망, 분산시스템/클라우드 학습 중.",
        "career": "스타트업/대기업 모두 경험, 성능 최적화/테스트 자동화 주도.",
        "vision": "비즈니스 임팩트 있는 기술 리더십 지향, 지식 공유/멘토링 선호.",
        "culture": "수평적 문화, 코드 품질·투명한 커뮤니케이션 중시."
    }
    job_summaries = {
        "roles": "이커머스 백엔드 마이크로서비스 설계·구현, 기술 이니셔티브 리드.",
        "skills": "Python/Java, REST API, SQL/NoSQL, AWS, Docker/K8s, 고트래픽 최적화.",
        "growth": "Principal/EM 성장 트랙, 학습 예산·신기술 프로젝트 제공.",
        "career": "점진적 책임 확대 및 멘토링 경험 선호, 기술적 우수성 요구.",
        "vision": "다음 세대 이커머스 플랫폼 구축, 확장성·신뢰성·혁신 중시.",
        "culture": "애자일, 코드 리뷰, 지식 공유, 워라밸·DEI 중시."
    }
    similarity_scores = {
        "roles": 0.92,
        "skills": 0.89,
        "growth": 0.87,
        "career": 0.91,
        "vision": 0.85,
        "culture": 0.88
    }

    final_explanation = generate_match_explanation(
        talent_summaries=talent_summaries,
        job_summaries=job_summaries,
        similarity_scores=similarity_scores
    )

    return MatchExplainResponse(
        job_fit=final_explanation.get("직무 적합성", {}),
        growth_potential=final_explanation.get("성장 가능성", {}),
        culture_fit=final_explanation.get("문화 적합성", {}),
        metadata=final_explanation.get("metadata", {})
    )
