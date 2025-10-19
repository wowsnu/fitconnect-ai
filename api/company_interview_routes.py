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

        # 생성된 JD 데이터 (캐싱용)
        self.generated_jd: Optional[dict] = None

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


class CreateJobPostingRequest(BaseModel):
    """채용공고 생성 요청"""
    session_id: str
    access_token: str


class SituationalAnalysisRequest(BaseModel):
    """Situational 분석 및 JD 생성 요청"""
    session_id: str
    access_token: str
    job_posting_id: Optional[int] = None  # 기존 JD가 있으면 해당 ID


class GenerateCardRequest(BaseModel):
    """카드 및 벡터 생성 요청"""
    session_id: str
    access_token: str
    job_posting_id: Optional[int] = None  # Optional: 없으면 새로 생성
    responsibilities: str
    requirements_must: str
    requirements_nice: str
    competencies: str


class StartSituationalRequest(BaseModel):
    """Situational 면접 시작 요청"""
    session_id: str


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
    full_company_profile = None
    try:
        company_profile = await backend_client.get_company_profile(
            access_token=request.access_token
        )
        full_company_profile = company_profile  # 전체 프로필 저장
        company_info = {
            "culture": company_profile.get("about", {}).get("culture"),
            "vision_mission": company_profile.get("about", {}).get("vision_mission"),
            "business_domains": company_profile.get("about", {}).get("business_domains"),
        }
        # 세션에 전체 회사 프로필 저장 (카드 생성 시 사용)
        session.company_info = full_company_profile
        print(f"[INFO] Loaded company info for dynamic questions")
        print(f"[DEBUG] company_profile structure: {full_company_profile.keys() if full_company_profile else 'None'}")
        if full_company_profile and "basic" in full_company_profile:
            print(f"[DEBUG] basic fields: {full_company_profile['basic'].keys()}")
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
        total_questions=8,  # 기술면접 총 8개 고정 (고정 5 + 동적 3)
        next_question=first_question,
        is_finished=False
    )


@company_interview_router.post("/technical/answer", response_model=AnswerResponse)
async def submit_company_technical_answer(request: AnswerRequest):
    """
    Technical 면접 답변 제출 (텍스트)

    고정 5개 완료 후 → 실시간 추천 질문 3개 자동 생성

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
        is_finished=result.get("is_finished", False)  # submit_answer의 is_finished 사용
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
async def start_company_situational_interview(request: StartSituationalRequest):
    """
    기업 Situational 면접 시작

    Args:
        request: session_id

    Returns:
        첫 질문 (고정 5개 중 첫번째)
    """
    # 세션 확인
    if request.session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[request.session_id]

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
        total_questions=8,  # 상황면접 총 8개 고정 (고정 5 + 동적 3)
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
        is_finished=result.get("is_finished", False)  # submit_answer의 is_finished 사용
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


@company_interview_router.post("/situational/analysis")
async def create_situational_analysis_with_jd(request: SituationalAnalysisRequest):
    """
    Situational 면접 분석 및 JD 생성 (백엔드에 POST 안 함, response만 반환)

    Args:
        request: session_id, access_token, job_posting_id (optional)

    Returns:
        생성된 JD 데이터 (responsibilities, requirements_must, requirements_nice, competencies)
    """
    # 세션 확인
    if request.session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[request.session_id]

    # 모든 면접 완료 확인
    if not session.general_interview.is_finished():
        raise HTTPException(status_code=400, detail="General interview not completed")

    if not session.technical_interview or not session.technical_interview.is_finished():
        raise HTTPException(status_code=400, detail="Technical interview not completed")

    if not session.situational_interview or not session.situational_interview.is_finished():
        raise HTTPException(status_code=400, detail="Situational interview not completed")

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

    # 기존 JD 가져오기 (job_posting_id가 있으면)
    existing_jd = None
    if request.job_posting_id:
        try:
            from ai.interview.client import get_backend_client
            backend_client = get_backend_client()
            existing_jd = await backend_client.get_job_posting(
                job_posting_id=request.job_posting_id,
                access_token=request.access_token
            )
            print(f"[INFO] Loaded existing JD for job posting {request.job_posting_id}")
        except Exception as e:
            print(f"[WARNING] Failed to load existing JD: {str(e)}")

    # 면접 결과를 JD 데이터로 변환
    from ai.interview.company.jd_generator import create_job_posting_from_interview

    job_posting_data = create_job_posting_from_interview(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        team_fit_analysis=session.situational_profile,
        company_profile=session.company_info,  # 기업 프로필 전달
        existing_jd=existing_jd  # 기존 JD 전달
    )

    # 기존 JD가 있으면 4개 필드만 업데이트
    if existing_jd:
        # 기존 데이터 유지하면서 4개 필드만 교체
        result_jd = existing_jd.copy()
        result_jd["responsibilities"] = job_posting_data["responsibilities"]
        result_jd["requirements_must"] = job_posting_data["requirements_must"]
        result_jd["requirements_nice"] = job_posting_data["requirements_nice"]
        result_jd["competencies"] = job_posting_data["competencies"]
    else:
        # 기존 JD가 없으면 전체 새로 생성
        result_jd = job_posting_data

    # 세션에 전체 JD 데이터 캐싱 (나중에 generate에서 사용)
    session.generated_jd = result_jd

    # 프론트엔드에는 4개 필드만 반환
    return {
        "success": True,
        "job_posting_data": {
            "responsibilities": result_jd["responsibilities"],
            "requirements_must": result_jd["requirements_must"],
            "requirements_nice": result_jd["requirements_nice"],
            "competencies": result_jd["competencies"]
        },
        "is_new": existing_jd is None
    }


@company_interview_router.post("/generate")
async def generate_card_and_vectors(request: GenerateCardRequest):
    """
    수정된 JD로 카드 및 매칭 벡터 생성

    Args:
        request: session_id, access_token, job_posting_id (optional), responsibilities, requirements_must, requirements_nice, competencies

    Returns:
        생성된 카드 및 벡터 정보
    """
    # 세션 확인
    if request.session_id not in company_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = company_sessions[request.session_id]

    # 분석 결과 확인
    if not session.general_analysis or not session.technical_requirements or not session.situational_profile:
        raise HTTPException(
            status_code=400,
            detail="Interview analysis not completed. Please call /situational/analysis first."
        )

    # 수정된 JD 데이터 구성
    updated_jd_data = session.generated_jd.copy() if session.generated_jd else {}
    updated_jd_data["responsibilities"] = request.responsibilities
    updated_jd_data["requirements_must"] = request.requirements_must
    updated_jd_data["requirements_nice"] = request.requirements_nice
    updated_jd_data["competencies"] = request.competencies

    # 백엔드 API enum에 맞게 location_city 정규화
    def normalize_location_city(location: str) -> str:
        """기업 프로필의 location을 백엔드 enum에 맞게 변환"""
        if not location:
            return "서울"

        # 허용되는 값 목록
        allowed = ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '강원', '충북', '충남', '전북', '전남', '경북', '경남']

        # 이미 허용된 값이면 그대로 반환
        if location in allowed:
            return location

        # 문자열에서 지역명 추출
        for region in allowed:
            if region in location:
                return region

        # 매칭 실패하면 기본값
        return "서울"

    # 기업 프로필에서 정보 추출 (없으면 기본값)
    if session.company_info:
        basic = session.company_info.get("basic", {})
        if "location_city" not in updated_jd_data or not updated_jd_data["location_city"]:
            raw_location = basic.get("location_city", "서울")
            updated_jd_data["location_city"] = normalize_location_city(raw_location)
        if "employment_type" not in updated_jd_data or not updated_jd_data["employment_type"]:
            updated_jd_data["employment_type"] = basic.get("employment_type", "정규직")
        if "career_level" not in updated_jd_data or not updated_jd_data["career_level"]:
            updated_jd_data["career_level"] = basic.get("career_level", "경력무관")
        if "education_level" not in updated_jd_data or not updated_jd_data["education_level"]:
            updated_jd_data["education_level"] = basic.get("education_level", "학력무관")

    # status는 항상 DRAFT로 설정
    updated_jd_data["status"] = "DRAFT"

    from ai.interview.client import get_backend_client
    backend_client = get_backend_client()

    job_posting_id = request.job_posting_id

    if job_posting_id:
        # 기존 JD가 있으면 4개 필드만 PATCH로 업데이트
        print(f"[INFO] Updating existing job posting {job_posting_id} with 4 fields...")
        updates = {
            "responsibilities": request.responsibilities,
            "requirements_must": request.requirements_must,
            "requirements_nice": request.requirements_nice,
            "competencies": request.competencies
        }
        await backend_client.update_job_posting(
            job_posting_id=job_posting_id,
            access_token=request.access_token,
            updates=updates
        )
        print(f"[INFO] Updated job posting {job_posting_id}")

        # PATCH 후 최신 JD 데이터를 다시 가져오기 (카드 생성에 사용)
        updated_job_posting = await backend_client.get_job_posting(
            job_posting_id=job_posting_id,
            access_token=request.access_token
        )
        updated_jd_data = updated_job_posting
    else:
        # 새로운 JD 생성
        print("[INFO] No job_posting_id provided. Creating new job posting...")
        print(f"[DEBUG] Job posting data to be sent: {updated_jd_data}")
        created_job_posting = await backend_client.create_job_posting(
            access_token=request.access_token,
            job_posting_data=updated_jd_data
        )
        job_posting_id = created_job_posting.get("id")
        print(f"[INFO] Created new job posting with ID: {job_posting_id}")

    # 카드 데이터 생성
    from ai.interview.company.jd_generator import create_job_posting_card_from_interview

    card_data = create_job_posting_card_from_interview(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        team_fit_analysis=session.situational_profile,
        job_posting_id=job_posting_id,
        company_name=session.company_name,
        job_posting_data=updated_jd_data,
        company_profile=session.company_info  # 회사 프로필 전달
    )

    # 백엔드에 카드 POST
    try:
        created_card = await backend_client.create_job_posting_card(
            access_token=request.access_token,
            card_data=card_data
        )
    except ValueError as e:
        if "409" in str(e) and job_posting_id:
            print(f"[INFO] Job posting card already exists for job_posting_id={job_posting_id}. Updating instead.")
            created_card = await backend_client.update_job_posting_card(
                job_posting_id=job_posting_id,
                access_token=request.access_token,
                card_data=card_data
            )
        else:
            raise

    # 매칭 벡터 생성
    from ai.matching.company_vector_generator import generate_company_matching_vectors

    matching_result = generate_company_matching_vectors(
        general_analysis=session.general_analysis,
        technical_requirements=session.technical_requirements,
        team_fit_analysis=session.situational_profile,
        company_name=session.company_name,
        job_posting_data=updated_jd_data
    )

    # 백엔드에 매칭 벡터 POST
    created_vectors = await backend_client.post_matching_vectors(
        vectors_data=matching_result["vectors"],
        access_token=request.access_token,
        role="company"
    )

    return {
        "success": True,
        "job_posting_id": job_posting_id,  # job_posting_id 추가
        "card_id": created_card.get("id"),
        "matching_vector_id": created_vectors.get("id"),
        "card": created_card,
        "matching_texts": matching_result["texts"]
    }


# ==================== Job Posting Card API ====================

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
