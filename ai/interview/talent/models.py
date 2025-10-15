"""
Interview System Pydantic Models
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# ==================== General Interview ====================

class GeneralInterviewAnalysis(BaseModel):
    """구조화 면접 답변 종합 분석 결과"""

    key_themes: List[str] = Field(
        description="답변에서 자주 언급된 주요 테마/키워드",
        max_length=5,
        default_factory=list,
    )

    interests: List[str] = Field(
        description="지원자가 관심있어하는 기술 분야",
        max_length=5,
        default_factory=list,
    )

    work_style_hints: List[str] = Field(
        description="답변에서 드러난 업무 스타일",
        max_length=5,
        default_factory=list,
    )

    emphasized_experiences: List[str] = Field(
        description="지원자가 자주 언급하거나 강조한 경험",
        max_length=5,
        default_factory=list,
    )

    technical_keywords: List[str] = Field(
        description="답변에서 언급된 기술 키워드",
        max_length=10,
        default_factory=list,
    )


# ==================== Technical Interview ====================

class TalentBasic(BaseModel):
    """인재 기본 정보"""
    user_id: int
    name: Optional[str] = None
    birth_date: Optional[str] = None
    phone: Optional[str] = None
    tagline: Optional[str] = None
    profile_step: Optional[int] = None
    is_submitted: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Experience(BaseModel):
    """경력 정보"""
    id: int
    user_id: int
    company_name: str
    title: str
    start_ym: Optional[str] = None
    end_ym: Optional[str] = None
    duration_years: Optional[int] = None
    leave_reason: Optional[str] = None
    summary: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Education(BaseModel):
    """학력 정보"""
    id: int
    user_id: int
    school_name: str
    major: Optional[str] = None
    status: str
    start_ym: Optional[str] = None
    end_ym: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Activity(BaseModel):
    """활동 정보"""
    id: int
    user_id: int
    name: str
    category: Optional[str] = None
    period_ym: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Certification(BaseModel):
    """자격증 정보"""
    id: int
    user_id: int
    name: str
    score_or_grade: Optional[str] = None
    acquired_ym: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Document(BaseModel):
    """문서 정보"""
    id: int
    user_id: int
    doc_type: str
    storage_url: str
    original_name: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CandidateProfile(BaseModel):
    """지원자 전체 프로필 (백엔드 API 응답 형식)"""

    basic: Optional[TalentBasic] = None
    experiences: List[Experience] = Field(default_factory=list)
    educations: List[Education] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    documents: List[Document] = Field(default_factory=list)


class InterviewQuestion(BaseModel):
    """면접 질문"""

    question: str = Field(
        description="면접 질문 (이전 답변을 바탕으로 자연스럽게 깊이 파고들기)",
        min_length=20,
        max_length=300,
    )

    skill: str = Field(
        description="평가 대상 기술",
    )

    why: str = Field(
        description="이 질문을 하는 이유 (채용 담당자용)",
        min_length=10
    )


class AnswerFeedback(BaseModel):
    """답변 피드백 (점수 없음)"""

    key_points: List[str] = Field(
        description="답변에서 발견된 주요 포인트 (다음 질문에 활용)",
        max_length=5,
        default_factory=list,
    )

    mentioned_technologies: List[str] = Field(
        description="답변에서 언급된 기술/도구",
        max_length=5,
        default_factory=list,
    )

    depth_areas: List[str] = Field(
        description="더 깊이 파고들 수 있는 영역",
        max_length=3,
        default_factory=list,
        examples=[["캐싱 전략", "동시성 처리", "성능 최적화"]]
    )

    follow_up_direction: str = Field(
        description="다음 질문에서 집중할 방향",
        examples=["Redis 캐싱 전략을 구체적으로 파고들기", "비동기 처리의 에러 핸들링 확인"]
    )


# ==================== Situational Interview ====================

class PersonaDimensions(BaseModel):
    """페르소나 5개 차원"""

    work_style: Literal["주도형", "협력형", "독립형"]
    problem_solving: Literal["분석형", "직관형", "실행형"]
    learning: Literal["체계형", "실험형", "관찰형"]
    stress_response: Literal["도전형", "안정형", "휴식형"]
    communication: Literal["논리형", "공감형", "간결형"]


class PersonaScores(BaseModel):
    """페르소나 점수 (각 차원별 점수)"""

    work_style: dict[str, float] = Field(default_factory=dict)
    problem_solving: dict[str, float] = Field(default_factory=dict)
    learning: dict[str, float] = Field(default_factory=dict)
    stress_response: dict[str, float] = Field(default_factory=dict)
    communication: dict[str, float] = Field(default_factory=dict)


class FinalPersonaReport(BaseModel):
    """최종 페르소나 리포트"""

    work_style: str
    work_style_reason: str = Field(description="업무 스타일 판단 근거")

    problem_solving: str
    problem_solving_reason: str = Field(description="문제 해결 방식 판단 근거")

    learning: str
    learning_reason: str = Field(description="학습 성향 판단 근거")

    stress_response: str
    stress_response_reason: str = Field(description="스트레스 대응 판단 근거")

    communication: str
    communication_reason: str = Field(description="커뮤니케이션 스타일 판단 근거")

    confidence: float = Field(ge=0, le=1, description="신뢰도 0-1")
    summary: str = Field(description="요약 (예: 협력적이며 논리적인 분석가형)")
    team_fit: str = Field(description="적합한 팀 환경")


class CompetencyItem(BaseModel):
    """역량 항목"""
    name: str = Field(description="역량명")
    level: str = Field(description="수준: 높음/보통/낮음")


class GeneralInterviewCardPart(BaseModel):
    """구조화 면접에서 추출한 카드 정보 (1, 3)"""

    key_experiences: list[str] = Field(
        description="주요 경험/경력 (4개)",
        min_length=4,
        max_length=4
    )

    core_competencies: list[CompetencyItem] = Field(
        description="핵심 일반 역량 (4개)",
        min_length=4,
        max_length=4
    )


class TechnicalInterviewCardPart(BaseModel):
    """직무적합성 면접에서 추출한 카드 정보 (2, 4)"""

    strengths: list[str] = Field(
        description="강점 (4개)",
        min_length=4,
        max_length=4
    )

    technical_skills: list[CompetencyItem] = Field(
        description="핵심 직무 역량/기술 (4개)",
        min_length=4,
        max_length=4
    )


class SituationalInterviewCardPart(BaseModel):
    """상황 면접에서 추출한 카드 정보 (5, 6, 7 + 보완)"""

    job_fit: str = Field(description="직무 적합성 요약")
    team_fit: str = Field(description="협업 성향 요약")
    growth_potential: str = Field(description="성장 가능성 요약")

    # 부족한 부분 보완 (Optional)
    additional_experiences: list[str] = Field(
        description="추가 주요 경험 (부족시)",
        default_factory=list
    )
    additional_strengths: list[str] = Field(
        description="추가 강점 (부족시)",
        default_factory=list
    )
    additional_competencies: list[CompetencyItem] = Field(
        description="추가 일반 역량 (부족시)",
        default_factory=list
    )
    additional_technical: list[CompetencyItem] = Field(
        description="추가 직무 역량 (부족시)",
        default_factory=list
    )


class CandidateProfileCard(BaseModel):
    """지원자 프로필 분석 카드"""

    candidate_name: str = Field(description="지원자 이름")
    role: str = Field(description="지원 직무")
    experience_years: float = Field(description="경력 연수")
    company: str = Field(description="현재 회사", default="")

    key_experiences: list[str] = Field(
        description="주요 경험/경력 (4개)",
        min_length=4,
        max_length=4
    )

    strengths: list[str] = Field(
        description="강점 (4개)",
        min_length=4,
        max_length=4
    )

    core_competencies: list[CompetencyItem] = Field(
        description="핵심 일반 역량 (4개)",
        min_length=4,
        max_length=4
    )

    technical_skills: list[CompetencyItem] = Field(
        description="핵심 직무 역량/기술 (4개)",
        min_length=4,
        max_length=4
    )

    job_fit: str = Field(description="직무 적합성 요약")
    team_fit: str = Field(description="협업 성향 요약")
    growth_potential: str = Field(description="성장 가능성 요약")
