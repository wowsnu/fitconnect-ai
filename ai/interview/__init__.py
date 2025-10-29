"""
AI Interview System

구조 개편:
- ai.interview.talent: 인재 인터뷰 모듈
- ai.interview.company: 기업 인터뷰 모듈
- ai.interview.client: 공통 백엔드 API 클라이언트

3가지 인터뷰 타입:
1. General Interview (구조화 면접) - 고정 질문 5-7개
2. Technical Interview (직무 적합성 면접) - 개인화된 질문
3. Situational Interview (상황 면접) - 페르소나 분석 6개 질문
"""

# Talent Interview 모듈
from ai.interview.talent import (
    GeneralInterviewAnalysis,
    CandidateProfile,
    CandidateProfileCard,
    PersonaScores,
    FinalPersonaReport,
    GeneralInterview,
    TechnicalInterview,
    SituationalInterview,
    analyze_general_interview,
    generate_candidate_profile_card,
)

# Company Interview 모듈
from ai.interview.company import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile,
    JobPostingCard,
    CompanyInfo,
    CompanyGeneralInterview,
    CompanyTechnicalInterview,
    CompanySituationalInterview,
    analyze_company_general_interview,
    analyze_company_technical_interview,
    analyze_company_situational_interview,
    create_job_posting_from_interview,
    create_job_posting_card_from_interview,
)

# 공통 모듈
from ai.interview.client import BackendAPIClient, get_backend_client

__all__ = [
    # Talent
    "GeneralInterviewAnalysis",
    "CandidateProfile",
    "CandidateProfileCard",
    "PersonaScores",
    "FinalPersonaReport",
    "GeneralInterview",
    "TechnicalInterview",
    "SituationalInterview",
    "analyze_general_interview",
    "generate_candidate_profile_card",
    # Company
    "CompanyGeneralAnalysis",
    "TechnicalRequirements",
    "TeamCultureProfile",
    "JobPostingCard",
    "CompanyInfo",
    "CompanyGeneralInterview",
    "CompanyTechnicalInterview",
    "CompanySituationalInterview",
    "analyze_company_general_interview",
    "analyze_company_technical_interview",
    "analyze_company_situational_interview",
    "create_job_posting_from_interview",
    "create_job_posting_card_from_interview",
    # Common
    "BackendAPIClient",
    "get_backend_client",
]
