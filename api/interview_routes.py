"""
Interview API Routes

프론트엔드 플로우:
1. POST /interview/general/start - 인터뷰 시작, 첫 질문 반환
2. POST /interview/general/answer - 음성 업로드, STT, 답변 저장, 다음 질문 반환
3. GET /interview/general/analysis/{session_id} - 최종 분석 결과
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from ai.interview.general import GeneralInterview, analyze_general_interview
from ai.interview.technical import TechnicalInterview
from ai.interview.situational import SituationalInterview
from ai.interview.profile_analysis import generate_candidate_profile_card
from ai.interview.models import CandidateProfile, CandidateProfileCard
from ai.interview.client import get_backend_client
from ai.stt.service import get_stt_service


# 라우터 생성
interview_router = APIRouter(prefix="/interview", tags=["Interview"])


# ==================== 세션 관리 (In-Memory) ====================
# TODO: 나중에 Redis 또는 DB로 교체
interview_sessions = {}


class InterviewSession:
    """인터뷰 세션 데이터"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.interview = GeneralInterview()
        self.general_analysis = None  # 구조화 면접 분석 결과
        self.technical_interview = None  # 직무 적합성 면접
        self.situational_interview = None  # 상황 면접
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


# ==================== Request/Response Models ====================

class StartInterviewResponse(BaseModel):
    """인터뷰 시작 응답"""
    session_id: str
    question: str
    question_number: int
    total_questions: int


class AnswerRequest(BaseModel):
    """답변 제출 요청 (텍스트 직접 입력용)"""
    session_id: str
    answer: str


class AnswerResponse(BaseModel):
    """답변 제출 응답"""
    success: bool
    question_number: int
    total_questions: int
    next_question: Optional[str] = None
    is_finished: bool


class AnalysisResponse(BaseModel):
    """최종 분석 결과"""
    session_id: str
    key_themes: list[str]
    interests: list[str]
    work_style_hints: list[str]
    emphasized_experiences: list[str]
    technical_keywords: list[str]


# ==================== API Endpoints ====================

@interview_router.post("/general/start", response_model=StartInterviewResponse)
async def start_general_interview():
    """
    구조화 면접 시작

    Returns:
        - session_id: 세션 ID (이후 요청에 사용)
        - question: 첫 번째 질문
        - question_number: 현재 질문 번호 (1)
        - total_questions: 전체 질문 수 (5)
    """
    # 세션 생성
    session_id = str(uuid.uuid4())
    session = InterviewSession(session_id)
    interview_sessions[session_id] = session

    # 첫 질문
    first_question = session.interview.get_next_question()

    return StartInterviewResponse(
        session_id=session_id,
        question=first_question,
        question_number=1,
        total_questions=len(session.interview.questions)
    )


@interview_router.post("/general/answer/text", response_model=AnswerResponse)
async def submit_text_answer(request: AnswerRequest):
    """
    텍스트 답변 제출 (개발/테스트용)

    Args:
        session_id: 세션 ID
        answer: 답변 텍스트

    Returns:
        - next_question: 다음 질문 (없으면 None)
        - is_finished: 모든 질문 완료 여부
    """
    # 세션 확인
    if request.session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[request.session_id]
    session.updated_at = datetime.now()

    # 답변 제출
    result = session.interview.submit_answer(request.answer)

    return AnswerResponse(
        success=True,
        question_number=result["question_number"],
        total_questions=result["total_questions"],
        next_question=result["next_question"],
        is_finished=session.interview.is_finished()
    )


@interview_router.post("/general/answer/audio", response_model=AnswerResponse)
async def submit_audio_answer(
    session_id: str,
    audio: UploadFile = File(...)
):
    """
    음성 답변 제출 (실제 사용)

    Args:
        session_id: 세션 ID
        audio: 음성 파일 (MP3, WAV, M4A 등)

    Returns:
        - next_question: 다음 질문
        - is_finished: 완료 여부
    """
    # 세션 확인
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]
    session.updated_at = datetime.now()

    # 음성 파일 저장 (임시)
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
        result = session.interview.submit_answer(answer_text)

        return AnswerResponse(
            success=True,
            question_number=result["question_number"],
            total_questions=result["total_questions"],
            next_question=result["next_question"],
            is_finished=session.interview.is_finished()
        )

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@interview_router.get("/general/analysis/{session_id}", response_model=AnalysisResponse)
async def get_analysis(session_id: str):
    """
    구조화 면접 분석 결과 조회

    Args:
        session_id: 세션 ID

    Returns:
        분석 결과 (key_themes, interests, technical_keywords 등)
    """
    # 세션 확인
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]

    # 완료 확인
    if not session.interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail=f"Interview not finished. {session.interview.current_index}/{len(session.interview.questions)} questions answered."
        )

    # 답변 분석
    answers = session.interview.get_answers()
    analysis = analyze_general_interview(answers)

    return AnalysisResponse(
        session_id=session_id,
        key_themes=analysis.key_themes,
        interests=analysis.interests,
        work_style_hints=analysis.work_style_hints,
        emphasized_experiences=analysis.emphasized_experiences,
        technical_keywords=analysis.technical_keywords
    )


@interview_router.get("/general/session/{session_id}")
async def get_session_info(session_id: str):
    """
    세션 정보 조회 (디버깅용)

    Args:
        session_id: 세션 ID

    Returns:
        세션 상태, 진행도 등
    """
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]

    return {
        "session_id": session_id,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "current_question": session.interview.current_index,
        "total_questions": len(session.interview.questions),
        "is_finished": session.interview.is_finished(),
        "answers_count": len(session.interview.answers)
    }


@interview_router.delete("/general/session/{session_id}")
async def delete_session(session_id: str):
    """
    세션 삭제

    Args:
        session_id: 세션 ID
    """
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del interview_sessions[session_id]

    return {"message": "Session deleted successfully"}


# ==================== Technical Interview APIs ====================

class StartTechnicalRequest(BaseModel):
    """직무 적합성 면접 시작 요청"""
    session_id: str
    access_token: str  # JWT 토큰 (백엔드 API 호출용)


class TechnicalQuestionResponse(BaseModel):
    """직무 면접 질문 응답"""
    skill: str
    question_number: int
    question: str
    why: str
    progress: str
    selected_skills: Optional[list[str]] = None  # 선정된 기술 리스트 (start시에만 포함)


class TechnicalAnswerRequest(BaseModel):
    """직무 면접 답변 제출"""
    session_id: str
    answer: str


class TechnicalAnswerResponse(BaseModel):
    """직무 면접 답변 응답"""
    feedback: dict  # 점수 없음, 피드백만
    next_question: Optional[TechnicalQuestionResponse] = None
    is_finished: bool


@interview_router.post("/technical/start", response_model=TechnicalQuestionResponse)
async def start_technical_interview(request: StartTechnicalRequest):
    """
    직무 적합성 면접 시작

    Args:
        session_id: 구조화 면접 세션 ID
        access_token: JWT 액세스 토큰 (백엔드 API 호출용)

    Returns:
        첫 질문
    """
    # 세션 확인
    if request.session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[request.session_id]

    # 구조화 면접 완료 확인
    if not session.interview.is_finished():
        raise HTTPException(
            status_code=400,
            detail="General interview must be completed first"
        )

    # 구조화 면접 분석 (아직 안했으면)
    if not session.general_analysis:
        answers = session.interview.get_answers()
        session.general_analysis = analyze_general_interview(answers)

    # 백엔드 API에서 프로필 가져오기
    backend_client = get_backend_client()
    try:
        # TODO: user_id는 세션에서 가져오거나 JWT에서 파싱
        user_id = 1  # 임시값
        profile = await backend_client.get_talent_profile(user_id, request.access_token)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch profile from backend: {str(e)}"
        )

    # Technical Interview 초기화
    session.technical_interview = TechnicalInterview(
        profile=profile,
        general_analysis=session.general_analysis
    )

    # 첫 질문
    first_question = session.technical_interview.get_next_question()

    return TechnicalQuestionResponse(
        **first_question,
        selected_skills=session.technical_interview.skills  # 선정된 기술 리스트 추가
    )


@interview_router.post("/technical/answer", response_model=TechnicalAnswerResponse)
async def submit_technical_answer(request: TechnicalAnswerRequest):
    """
    직무 면접 답변 제출 (텍스트)

    Args:
        session_id: 세션 ID
        answer: 답변

    Returns:
        평가 결과 + 다음 질문
    """
    # 세션 확인
    if request.session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[request.session_id]

    # Technical Interview 확인
    if not session.technical_interview:
        raise HTTPException(
            status_code=400,
            detail="Technical interview not started"
        )

    # 답변 제출
    result = session.technical_interview.submit_answer(request.answer)

    next_q = result["next_question"]
    next_question_response = TechnicalQuestionResponse(**next_q) if next_q else None

    return TechnicalAnswerResponse(
        feedback=result["feedback"],
        next_question=next_question_response,
        is_finished=session.technical_interview.is_finished()
    )


@interview_router.post("/technical/answer/audio", response_model=TechnicalAnswerResponse)
async def submit_technical_answer_audio(
    session_id: str,
    audio: UploadFile = File(...)
):
    """
    직무 면접 답변 제출 (음성)

    Args:
        session_id: 세션 ID
        audio: 음성 파일 (webm, mp3, wav 등)

    Returns:
        평가 결과 + 다음 질문
    """
    # 세션 확인
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]

    # Technical Interview 확인
    if not session.technical_interview:
        raise HTTPException(
            status_code=400,
            detail="Technical interview not started"
        )

    # 음성 파일 저장 (임시)
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
        result = session.technical_interview.submit_answer(answer_text)

        next_q = result["next_question"]
        next_question_response = TechnicalQuestionResponse(**next_q) if next_q else None

        return TechnicalAnswerResponse(
            feedback=result["feedback"],
            next_question=next_question_response,
            is_finished=session.technical_interview.is_finished()
        )

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@interview_router.get("/technical/results/{session_id}")
async def get_technical_results(session_id: str):
    """
    직무 면접 결과 조회

    Args:
        session_id: 세션 ID

    Returns:
        평가 결과 (기술별 점수, 평균 등)
    """
    # 세션 확인
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]

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
            detail=f"Technical interview not finished. {session.technical_interview.get_total_answered()}/9 questions answered."
        )

    return session.technical_interview.get_results()


# ==================== Situational Interview APIs ====================

class SituationalQuestionResponse(BaseModel):
    """상황 면접 질문 응답"""
    question: str
    phase: str  # exploration, deep_dive, validation
    progress: str  # "1/6", "2/6", ...


class SituationalAnswerRequest(BaseModel):
    """상황 면접 답변 제출"""
    session_id: str
    answer: str


class SituationalAnswerResponse(BaseModel):
    """상황 면접 답변 응답"""
    analysis: dict  # reasoning, detected_traits
    next_question: Optional[SituationalQuestionResponse] = None
    is_finished: bool


class PersonaReportResponse(BaseModel):
    """페르소나 리포트 응답"""
    persona: dict  # 5개 차원별 성향
    summary: str
    recommended_team_environment: str


@interview_router.post("/situational/start", response_model=SituationalQuestionResponse)
async def start_situational_interview(
    session_id: str = Query(..., description="세션 ID"),
    skip_validation: bool = Query(False, description="True면 이전 면접 체크 스킵 (테스트용)")
):
    """
    상황 면접 시작

    Args:
        session_id: 직무 적합성 면접 세션 ID
        skip_validation: True면 이전 면접 완료 체크 스킵 (테스트용)

    Returns:
        첫 질문 (탐색 단계)
    """
    # 세션 확인 (없으면 새로 생성)
    if session_id not in interview_sessions:
        if skip_validation:
            # 테스트용: 새 세션 생성
            session = InterviewSession(session_id)
            interview_sessions[session_id] = session
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = interview_sessions[session_id]

    # 직무 적합성 면접 완료 확인 (skip_validation=True면 스킵)
    if not skip_validation:
        if not session.technical_interview or not session.technical_interview.is_finished():
            raise HTTPException(
                status_code=400,
                detail="Technical interview must be completed first"
            )

    # Situational Interview 초기화
    session.situational_interview = SituationalInterview()

    # 첫 질문
    first_question = session.situational_interview.get_next_question()

    return SituationalQuestionResponse(**first_question)


@interview_router.post("/situational/answer", response_model=SituationalAnswerResponse)
async def submit_situational_answer(request: SituationalAnswerRequest):
    """
    상황 면접 답변 제출 (텍스트)

    Args:
        session_id: 세션 ID
        answer: 답변

    Returns:
        분석 결과 + 다음 질문
    """
    # 세션 확인
    if request.session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[request.session_id]

    # Situational Interview 확인
    if not session.situational_interview:
        raise HTTPException(
            status_code=400,
            detail="Situational interview not started"
        )

    # 답변 제출
    result = session.situational_interview.submit_answer(request.answer)

    next_q = result["next_question"]
    next_question_response = SituationalQuestionResponse(**next_q) if next_q else None

    return SituationalAnswerResponse(
        analysis=result["analysis"],
        next_question=next_question_response,
        is_finished=session.situational_interview.is_finished()
    )


@interview_router.post("/situational/answer/audio", response_model=SituationalAnswerResponse)
async def submit_situational_answer_audio(
    session_id: str,
    audio: UploadFile = File(...)
):
    """
    상황 면접 답변 제출 (음성)

    Args:
        session_id: 세션 ID
        audio: 음성 파일 (webm, mp3, wav 등)

    Returns:
        분석 결과 + 다음 질문
    """
    # 세션 확인
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]

    # Situational Interview 확인
    if not session.situational_interview:
        raise HTTPException(
            status_code=400,
            detail="Situational interview not started"
        )

    # 음성 파일 저장 (임시)
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
        result = session.situational_interview.submit_answer(answer_text)

        next_q = result["next_question"]
        next_question_response = SituationalQuestionResponse(**next_q) if next_q else None

        return SituationalAnswerResponse(
            analysis=result["analysis"],
            next_question=next_question_response,
            is_finished=session.situational_interview.is_finished()
        )

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@interview_router.get("/situational/report/{session_id}", response_model=PersonaReportResponse)
async def get_persona_report(session_id: str):
    """
    페르소나 리포트 조회

    Args:
        session_id: 세션 ID

    Returns:
        최종 페르소나 분석 결과
    """
    # 세션 확인
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]

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
            detail=f"Situational interview not finished. {session.situational_interview.current_question_num}/6 questions answered."
        )

    # 최종 리포트 생성
    report = session.situational_interview.get_final_report()

    # persona를 dict로 변환
    persona_dict = {
        "work_style": report.work_style,
        "problem_solving": report.problem_solving,
        "learning": report.learning,
        "stress_response": report.stress_response,
        "communication": report.communication,
        "confidence": report.confidence
    }

    return PersonaReportResponse(
        persona=persona_dict,
        summary=report.summary,
        recommended_team_environment=report.team_fit
    )


@interview_router.get("/profile-card/{session_id}", response_model=CandidateProfileCard)
async def get_profile_card(session_id: str):
    """
    프로필 분석 카드 조회

    모든 면접(General + Technical + Situational)이 완료된 후 호출
    3가지 면접 결과를 종합하여 프로필 카드 생성

    Args:
        session_id: 세션 ID

    Returns:
        CandidateProfileCard (주요 경험, 강점, 역량 등)
    """
    # 세션 확인
    if session_id not in interview_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = interview_sessions[session_id]

    # 모든 면접 완료 확인
    if not session.interview.is_finished():
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

    # 일반 면접 분석 (캐시 확인)
    if not session.general_analysis:
        answers = session.interview.get_answers()
        session.general_analysis = analyze_general_interview(answers)

    # 상황 면접 리포트 생성
    situational_report = session.situational_interview.get_final_report()

    # 기술 면접 결과 (간단하게)
    technical_results = session.technical_interview.get_results() if session.technical_interview else {}

    # 프로필 카드 생성 (분석 결과만 사용)
    profile_card = generate_candidate_profile_card(
        candidate_profile=session.technical_interview.profile,
        general_analysis=session.general_analysis,
        technical_results=technical_results,
        situational_report=situational_report
    )

    return profile_card
