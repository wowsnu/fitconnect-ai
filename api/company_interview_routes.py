"""
Company Interview API Routes

기업 면접 플로우:
1. POST /company-interview/general/start - General 면접 시작
2. POST /company-interview/general/answer - 답변 제출 (텍스트 또는 음성)
3. GET /company-interview/general/analysis/{session_id} - General 분석 결과
4. POST /company-interview/technical/start - Technical 면접 시작 (실시간 추천 포함)
5. POST /company-interview/technical/answer - Technical 답변 제출
6. POST /company-interview/situational/start - Situational 면접 시작
7. POST /company-interview/situational/answer - Situational 답변 제출
8. GET /company-interview/job-posting/{session_id} - 최종 Job Posting Card 생성
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
from datetime import datetime

from ai.interview.company.general import (
    CompanyGeneralInterview,
    analyze_company_general_interview
)
from ai.interview.company.technical import (
    CompanyTechnicalInterview,
    analyze_company_technical_interview
)
from ai.interview.company.situational import (
    CompanySituationalInterview,
    analyze_company_situational_interview
)
from ai.interview.company.models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile,
    JobPostingCard
)
from ai.stt.service import get_stt_service


# 라우터 생성
company_interview_router = APIRouter(
    prefix="/company-interview",
    tags=["Company Interview"]
)


# ==================== 세션 관리 (In-Memory) ====================
# TODO: Redis 또는 DB로 교체
company_sessions = {}


class CompanyInterviewSession:
    """기업 면접 세션 데이터"""
    def __init__(self, session_id: str, company_name: str, existing_jd: Optional[str] = None):
        self.session_id = session_id
        self.company_name = company_name
        self.existing_jd = existing_jd
        self.company_info: Optional[dict] = None  # 기업 정보 (Technical에서 로드)

        # 면접 인스턴스
        self.general_interview = CompanyGeneralInterview()
        self.technical_interview = None
        self.situational_interview = None

        # 분석 결과
        self.general_analysis: Optional[CompanyGeneralAnalysis] = None
        self.technical_requirements: Optional[TechnicalRequirements] = None
        self.situational_profile: Optional[TeamCultureProfile] = None

        # 타임스탬프
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


# ==================== Request/Response Models ====================

class StartCompanyInterviewRequest(BaseModel):
    """기업 면접 시작 요청"""
    access_token: str
    company_name: Optional[str] = None  # 선택: 없으면 백엔드에서 자동 로드
    existing_jd: Optional[str] = None  # 기존 JD (선택, deprecated - Technical에서 job_posting_id 사용 권장)


class StartInterviewResponse(BaseModel):
    """면접 시작 응답"""
    session_id: str
    question: str
    question_number: int
    total_questions: int


class AnswerRequest(BaseModel):
    """답변 제출 요청"""
    session_id: str
    answer: str


class StartTechnicalInterviewRequest(BaseModel):
    """기업 Technical 면접 시작 요청"""
    session_id: str
    access_token: str
    job_posting_id: Optional[int] = None  # 선택: 없으면 JD 없이 진행


class AnswerResponse(BaseModel):
    """답변 제출 응답"""
    success: bool
    question_number: int
    total_questions: int
    next_question: Optional[str | Dict] = None  # str or dict (동적 질문)
    is_finished: bool


class GeneralAnalysisResponse(BaseModel):
    """General 분석 결과"""
    session_id: str
    core_values: list[str]
    ideal_candidate_traits: list[str]
    team_culture: str
    work_style: str
    hiring_reason: str


# ==================== General Interview APIs ====================

@company_interview_router.post("/general/start", response_model=StartInterviewResponse)
async def start_company_general_interview(request: StartCompanyInterviewRequest):
    """
    기업 General 면접 시작

    Args:
        request: access_token, company_name (optional), existing_jd (optional)

    Returns:
        session_id, 첫 질문
    """
    # 회사명 가져오기 (없으면 백엔드에서 로드)
    company_name = request.company_name
    if not company_name:
        try:
            from ai.interview.client import get_backend_client

            backend_client = get_backend_client()
            company_profile = await backend_client.get_company_profile(
                access_token=request.access_token
            )
            company_name = company_profile.get("basic", {}).get("name", "기업")
            print(f"[INFO] Loaded company name from backend: {company_name}")
        except Exception as e:
            print(f"[WARNING] Failed to load company profile: {str(e)}")
            company_name = "기업"  # 기본값

    # 세션 생성
    session_id = str(uuid.uuid4())
    session = CompanyInterviewSession(
        session_id=session_id,
        company_name=company_name,
        existing_jd=request.existing_jd
    )
    company_sessions[session_id] = session

    # 첫 질문
    first_question = session.general_interview.get_next_question()

    return StartInterviewResponse(
        session_id=session_id,
        question=first_question,
        question_number=1,
        total_questions=len(session.general_interview.questions)
    )


@company_interview_router.post("/general/answer", response_model=AnswerResponse)
async def submit_company_general_answer(request: AnswerRequest):
    """
    General 면접 답변 제출 (텍스트)

    Args:
        session_id: 세션 ID
        answer: 답변 텍스트

    Returns:
        다음 질문 또는 완료 상태
    """
    # 세션 확인
    if request.session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[request.session_id]
    session.updated_at = datetime.now()

    # 답변 제출
    result = session.general_interview.submit_answer(request.answer)

    return AnswerResponse(
        success=True,
        question_number=result["question_number"],
        total_questions=result["total_questions"],
        next_question=result["next_question"],
        is_finished=session.general_interview.is_finished()
    )


@company_interview_router.post("/general/answer/audio", response_model=AnswerResponse)
async def submit_company_general_answer_audio(
    session_id: str,
    audio: UploadFile = File(...)
):
    """
    General 면접 답변 제출 (음성)

    Args:
        session_id: 세션 ID
        audio: 음성 파일

    Returns:
        다음 질문 또는 완료 상태
    """
    # 세션 확인
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[session_id]
    session.updated_at = datetime.now()

    # 음성 파일 처리
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename)[1]) as tmp_file:
        content = await audio.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # STT 처리
        stt_service = get_stt_service()
        answer_text = stt_service.transcribe(tmp_path)

        # 답변 제출
        result = session.general_interview.submit_answer(answer_text)

        return AnswerResponse(
            success=True,
            question_number=result["question_number"],
            total_questions=result["total_questions"],
            next_question=result["next_question"],
            is_finished=session.general_interview.is_finished()
        )

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@company_interview_router.get("/general/analysis/{session_id}", response_model=GeneralAnalysisResponse)
async def get_company_general_analysis(session_id: str):
    """
    General 면접 분석 결과 조회

    Args:
        session_id: 세션 ID

    Returns:
        CompanyGeneralAnalysis
    """
    # 세션 확인
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[session_id]

    # 완료 확인
    if not session.general_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail=f"General interview not finished. {session.general_interview.current_index}/{len(session.general_interview.questions)} answered."
        )

    # 분석 수행 (캐시 확인)
    if not session.general_analysis:
        answers = session.general_interview.get_answers()
        session.general_analysis = analyze_company_general_interview(answers)

    return GeneralAnalysisResponse(
        session_id=session_id,
        core_values=session.general_analysis.core_values,
        ideal_candidate_traits=session.general_analysis.ideal_candidate_traits,
        team_culture=session.general_analysis.team_culture,
        work_style=session.general_analysis.work_style,
        hiring_reason=session.general_analysis.hiring_reason
    )


# ==================== Technical Interview APIs ====================

@company_interview_router.post("/technical/start", response_model=AnswerResponse)
async def start_company_technical_interview(request: StartTechnicalInterviewRequest):
    """
    기업 Technical 면접 시작

    Args:
        request: session_id, access_token, job_posting_id (optional)

    Returns:
        첫 질문 (고정 5개 중 첫번째)
    """
    # 세션 확인
    if request.session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[request.session_id]

    # General 면접 완료 확인
    if not session.general_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="General interview must be completed first"
        )

    # General 분석 (없으면 수행)
    if not session.general_analysis:
        answers = session.general_interview.get_answers()
        session.general_analysis = analyze_company_general_interview(answers)

    # 기업 정보 및 JD 가져오기
    from ai.interview.client import get_backend_client
    from ai.interview.company.technical import format_job_posting_to_jd

    backend_client = get_backend_client()

    # 1. 기업 정보 가져오기
    company_info = None
    try:
        company_profile = await backend_client.get_company_profile(
            access_token=request.access_token
        )
        company_info = {
            "culture": company_profile.get("about", {}).get("culture"),
            "vision_mission": company_profile.get("about", {}).get("vision_mission"),
            "business_domains": company_profile.get("about", {}).get("business_domains"),
        }
        print(f"[INFO] Loaded company info for dynamic questions")
    except Exception as e:
        print(f"[WARNING] Failed to load company profile: {str(e)}")

    # 2. JD 가져오기 (job_posting_id가 있으면)
    existing_jd = None
    if request.job_posting_id:
        try:
            job_posting = await backend_client.get_job_posting(
                job_posting_id=request.job_posting_id,
                access_token=request.access_token
            )
            existing_jd = format_job_posting_to_jd(job_posting)
            print(f"[INFO] Loaded JD for job posting {request.job_posting_id}")
        except Exception as e:
            print(f"[WARNING] Failed to load job posting: {str(e)}")

    # Technical Interview 초기화
    session.technical_interview = CompanyTechnicalInterview(
        general_analysis=session.general_analysis,
        existing_jd=existing_jd,
        company_info=company_info
    )

    # 첫 질문
    first_question = session.technical_interview.get_next_question()

    return AnswerResponse(
        success=True,
        question_number=first_question["number"],
        total_questions=first_question["total_fixed"],
        next_question=first_question,
        is_finished=False
    )


@company_interview_router.post("/technical/answer", response_model=AnswerResponse)
async def submit_company_technical_answer(request: AnswerRequest):
    """
    Technical 면접 답변 제출 (텍스트)

    고정 5개 완료 후 → 실시간 추천 질문 2-3개 자동 생성

    Args:
        session_id: 세션 ID
        answer: 답변 텍스트

    Returns:
        다음 질문 (고정 또는 동적)
    """
    # 세션 확인
    if request.session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[request.session_id]

    # Technical Interview 확인
    if not session.technical_interview:
        raise HTTPException(
            status_code=400,
            detail="Technical interview not started"
        )

    # 답변 제출
    result = session.technical_interview.submit_answer(request.answer)

    return AnswerResponse(
        success=True,
        question_number=result["question_number"],
        total_questions=result["total_questions"],
        next_question=result["next_question"],
        is_finished=session.technical_interview.is_finished()
    )


@company_interview_router.get("/technical/analysis/{session_id}")
async def get_company_technical_analysis(session_id: str):
    """
    Technical 면접 분석 결과 조회

    Args:
        session_id: 세션 ID

    Returns:
        TechnicalRequirements
    """
    # 세션 확인
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[session_id]

    # Technical Interview 확인
    if not session.technical_interview:
        raise HTTPException(
            status_code=400,
            detail="Technical interview not started"
        )

    # 완료 확인
    if not session.technical_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="Technical interview not finished"
        )

    # 분석 수행 (캐시 확인)
    if not session.technical_requirements:
        answers = session.technical_interview.get_answers()
        session.technical_requirements = analyze_company_technical_interview(
            answers=answers,
            general_analysis=session.general_analysis
        )

    return session.technical_requirements


# ==================== Situational Interview APIs ====================

@company_interview_router.post("/situational/start", response_model=AnswerResponse)
async def start_company_situational_interview(session_id: str):
    """
    기업 Situational 면접 시작

    Args:
        session_id: Technical 면접 세션 ID

    Returns:
        첫 질문 (고정 5개 중 첫번째)
    """
    # 세션 확인
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[session_id]

    # Technical 면접 완료 확인
    if not session.technical_interview or not session.technical_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="Technical interview must be completed first"
        )

    # Technical 분석 (없으면 수행)
    if not session.technical_requirements:
        answers = session.technical_interview.get_answers()
        session.technical_requirements = analyze_company_technical_interview(
            answers=answers,
            general_analysis=session.general_analysis
        )

    # Situational Interview 초기화
    session.situational_interview = CompanySituationalInterview(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        company_info=session.company_info
    )

    # 첫 질문
    first_question = session.situational_interview.get_next_question()

    return AnswerResponse(
        success=True,
        question_number=first_question["number"],
        total_questions=first_question["total_fixed"],
        next_question=first_question,
        is_finished=False
    )


@company_interview_router.post("/situational/answer", response_model=AnswerResponse)
async def submit_company_situational_answer(request: AnswerRequest):
    """
    Situational 면접 답변 제출 (텍스트)

    고정 5개 완료 후 → 실시간 추천 질문 2-3개 자동 생성

    Args:
        session_id: 세션 ID
        answer: 답변 텍스트

    Returns:
        다음 질문 (고정 또는 동적)
    """
    # 세션 확인
    if request.session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[request.session_id]

    # Situational Interview 확인
    if not session.situational_interview:
        raise HTTPException(
            status_code=400,
            detail="Situational interview not started"
        )

    # 답변 제출
    result = session.situational_interview.submit_answer(request.answer)

    return AnswerResponse(
        success=True,
        question_number=result["question_number"],
        total_questions=result["total_questions"],
        next_question=result["next_question"],
        is_finished=session.situational_interview.is_finished()
    )


@company_interview_router.get("/situational/analysis/{session_id}")
async def get_company_situational_analysis(session_id: str):
    """
    Situational 면접 분석 결과 조회

    Args:
        session_id: 세션 ID

    Returns:
        TeamCultureProfile
    """
    # 세션 확인
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[session_id]

    # Situational Interview 확인
    if not session.situational_interview:
        raise HTTPException(
            status_code=400,
            detail="Situational interview not started"
        )

    # 완료 확인
    if not session.situational_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="Situational interview not finished"
        )

    # 분석 수행 (캐시 확인)
    if not session.situational_profile:
        answers = session.situational_interview.get_answers()
        session.situational_profile = analyze_company_situational_interview(
            answers=answers,
            general_analysis=session.general_analysis,
            technical_requirements=session.technical_requirements
        )

    return session.situational_profile


# ==================== Job Posting Card API ====================

@company_interview_router.post("/job-posting")
async def create_job_posting_from_interview(
    session_id: str,
    access_token: str
):
    """
    면접 결과를 백엔드에 채용공고로 저장

    모든 면접(General + Technical + Situational) 완료 후 호출

    Args:
        session_id: 세션 ID
        access_token: JWT 액세스 토큰

    Returns:
        생성된 채용공고 정보
    """
    # 세션 확인
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[session_id]

    # 모든 면접 완료 확인
    if not session.general_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="General interview not completed"
        )

    if not session.technical_interview or not session.technical_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="Technical interview not completed"
        )

    if not session.situational_interview or not session.situational_interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="Situational interview not completed"
        )

    # 각 단계 분석 수행 (캐시 확인)
    if not session.general_analysis:
        answers = session.general_interview.get_answers()
        session.general_analysis = analyze_company_general_interview(answers)

    if not session.technical_requirements:
        answers = session.technical_interview.get_answers()
        session.technical_requirements = analyze_company_technical_interview(
            answers=answers,
            general_analysis=session.general_analysis
        )

    if not session.situational_profile:
        answers = session.situational_interview.get_answers()
        session.situational_profile = analyze_company_situational_interview(
            answers=answers,
            general_analysis=session.general_analysis,
            technical_requirements=session.technical_requirements
        )

    # 면접 결과를 JD 데이터로 변환
    from ai.interview.company.jd_generator import create_job_posting_from_interview

    job_posting_data = create_job_posting_from_interview(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        team_fit_analysis=session.situational_profile
    )

    # 백엔드에 JD POST
    from ai.interview.client import get_backend_client

    backend_client = get_backend_client()
    created_job_posting = await backend_client.create_job_posting(
        access_token=access_token,
        job_posting_data=job_posting_data
    )

    job_posting_id = created_job_posting.get("id")

    # 카드 데이터 생성 및 POST
    from ai.interview.company.jd_generator import create_job_posting_card_from_interview

    card_data = create_job_posting_card_from_interview(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        team_fit_analysis=session.situational_profile,
        job_posting_id=job_posting_id,
        company_name=session.company_name,
        job_posting_data=job_posting_data
    )

    created_card = await backend_client.create_job_posting_card(
        access_token=access_token,
        card_data=card_data
    )

    # 매칭 벡터 생성 및 POST
    from ai.matching.company_vector_generator import generate_company_matching_vectors

    matching_result = generate_company_matching_vectors(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        team_fit_analysis=session.situational_profile,
        company_name=session.company_name,
        job_posting_data=job_posting_data
    )

    # 백엔드에 매칭 벡터 POST
    created_vectors = await backend_client.post_matching_vectors(
        vectors_data=matching_result["vectors"],
        access_token=access_token,
        role="company"
    )

    return {
        "success": True,
        "job_posting_id": job_posting_id,
        "card_id": created_card.get("id"),
        "matching_vector_id": created_vectors.get("id"),
        "job_posting": created_job_posting,
        "card": created_card,
        "matching_texts": matching_result["texts"]
    }


# ==================== Session Management APIs ====================

@company_interview_router.get("/session/{session_id}")
async def get_company_session_info(session_id: str):
    """
    세션 정보 조회 (디버깅용)

    Args:
        session_id: 세션 ID

    Returns:
        세션 상태, 진행도 등
    """
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[session_id]

    return {
        "session_id": session_id,
        "company_name": session.company_name,
        "has_existing_jd": session.existing_jd is not None,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "general": {
            "current": session.general_interview.current_index,
            "total": len(session.general_interview.questions),
            "finished": session.general_interview.is_finished()
        },
        "technical": {
            "started": session.technical_interview is not None,
            "finished": session.technical_interview.is_finished() if session.technical_interview else False
        },
        "situational": {
            "started": session.situational_interview is not None,
            "finished": session.situational_interview.is_finished() if session.situational_interview else False
        }
    }


@company_interview_router.delete("/session/{session_id}")
async def delete_company_session(session_id: str):
    """
    세션 삭제

    Args:
        session_id: 세션 ID
    """
    if session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del company_sessions[session_id]

    return {"message": "Session deleted successfully"}
