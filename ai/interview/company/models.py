"""
Company Interview System Pydantic Models
기업 면접 시스템용 데이터 모델
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ==================== General Interview ====================

class CompanyGeneralAnalysis(BaseModel):
    """General 면접 분석 결과 (HR 관점)"""

    core_values: List[str] = Field(
        description="회사/팀의 핵심 가치",
        max_length=5,
        default_factory=list
    )

    ideal_candidate_traits: List[str] = Field(
        description="이상적인 인재 특징 (3-5가지)",
        min_length=3,
        max_length=5,
        default_factory=list
    )

    team_culture: str = Field(
        description="팀 문화 설명"
    )

    work_style: str = Field(
        description="팀의 업무 방식"
    )

    hiring_reason: str = Field(
        description="채용 이유/목적"
    )

    hiring_reason_reasoning: str = Field(
        description="채용 이유 심층 분석",
        default=""
    )


# ==================== Technical Interview ====================

class TechnicalRequirements(BaseModel):
    """Technical 면접 분석 결과 (직무 관점)"""

    job_title: str = Field(
        description="직무명"
    )

    main_responsibilities: List[str] = Field(
        description="주요 업무 (3~8개)",
        min_length=3,
        max_length=8,
        default_factory=list
    )

    required_skills: List[str] = Field(
        description="필수 역량 (3~8개)",
        min_length=3,
        max_length=8,
        default_factory=list
    )

    preferred_skills: List[str] = Field(
        description="우대 역량 (3~8개)",
        min_length=3,
        max_length=8,
        default_factory=list
    )

    expected_challenges: str = Field(
        description="예상되는 어려움/도전 과제"
    )

    expected_challenges_reasoning: str = Field(
        description="예상 도전 과제 심층 분석",
        default=""
    )


# ==================== Situational Interview ====================

class TeamCultureProfile(BaseModel):
    """Situational 면접 분석 결과 (팀 문화)"""

    team_situation: str = Field(
        description="팀 현황 (성장기, 안정기 등)"
    )

    team_situation_reasoning: str = Field(
        description="팀 현황 심층 분석",
        default=""
    )

    collaboration_style: str = Field(
        description="선호하는 협업 스타일"
    )

    collaboration_style_reasoning: str = Field(
        description="협업 스타일 심층 분석",
        default=""
    )

    conflict_resolution: str = Field(
        description="갈등 해결 방식"
    )

    conflict_resolution_reasoning: str = Field(
        description="갈등 해결 심층 분석",
        default=""
    )

    work_environment: str = Field(
        description="업무 환경 특성 (변화 vs 안정)"
    )

    work_environment_reasoning: str = Field(
        description="업무 환경 심층 분석",
        default=""
    )

    preferred_work_style: str = Field(
        description="선호하는 업무 스타일 (독립 vs 협업)"
    )

    preferred_work_style_reasoning: str = Field(
        description="선호 업무 스타일 심층 분석",
        default=""
    )


# ==================== Final Output ====================

class CompanyInfo(BaseModel):
    """기업 정보"""

    funding_stage: Optional[str] = Field(
        description="투자 단계 (예: Series B)",
        default=None
    )

    company_culture: str = Field(
        description="조직 문화 설명"
    )

    benefits: List[str] = Field(
        description="복리후생",
        default_factory=list
    )


class JobPostingCard(BaseModel):
    """최종 채용 공고 카드"""

    # === 헤더 정보 ===
    company_name: str = Field(description="회사명")
    position_title: str = Field(description="포지션명")
    deadline: Optional[str] = Field(description="마감일", default=None)

    # === 공고 정보 박스 ===
    experience_level: str = Field(
        description="경력 (예: '경력직 3-5년차')"
    )
    contract_duration: Optional[str] = Field(
        description="근무 기간 (예: '6개월')",
        default=None
    )
    department: str = Field(
        description="근무 부서 (예: '개발팀')"
    )
    employment_type: str = Field(
        description="고용 형태 (예: '정규직', '계약직')"
    )
    salary_info: Optional[str] = Field(
        description="연봉 정보 (예: '연봉 협상')",
        default=None
    )

    # === 주요 역할/업무 ===
    main_responsibilities: List[str] = Field(
        description="주요 역할/업무 (4개)",
        min_length=4,
        max_length=4
    )

    # === 자격 요건 ===
    required_skills: List[str] = Field(
        description="필수 역량 (4개)",
        min_length=4,
        max_length=4
    )

    # === 요구 역량 ===
    preferred_skills: List[str] = Field(
        description="우대 역량 (4개)",
        min_length=4,
        max_length=4
    )

    # === 기업 정보 ===
    company_info: CompanyInfo = Field(
        description="기업 정보 (투자 단계, 문화, 복리후생)"
    )

    # === 인재상 ===
    personality_fit: str = Field(
        description="적합한 성향/인재상 설명"
    )

    # === 도전 과제 ===
    challenges: str = Field(
        description="예상되는 어려움 및 성장 기회"
    )


# ==================== Interview Questions ====================

class CompanyInterviewQuestion(BaseModel):
    """기업 면접 질문"""

    question: str = Field(
        description="면접 질문",
        min_length=10,
        max_length=300
    )

    purpose: str = Field(
        description="질문 목적 (무엇을 파악하기 위한 질문인지)"
    )

    question_type: str = Field(
        description="질문 유형: 'fixed' 또는 'dynamic'"
    )


class RecommendedQuestions(BaseModel):
    """실시간 추천 질문 목록"""

    questions: List[CompanyInterviewQuestion] = Field(
        description="추천 질문 목록 (2-3개)",
        min_length=2,
        max_length=3
    )

    reasoning: str = Field(
        description="이 질문들을 추천한 이유"
    )
