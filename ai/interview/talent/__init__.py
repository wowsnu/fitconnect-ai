"""
Talent Interview Module

인재 인터뷰 관련 모듈:
- General Interview: 구조화 면접
- Technical Interview: 직무 적합성 면접
- Situational Interview: 상황 면접
- Profile Analysis: 프로필 분석 및 카드 생성
"""

from ai.interview.talent.models import (
    GeneralInterviewAnalysis,
    CandidateProfile,
    CandidateProfileCard,
    PersonaScores,
    FinalPersonaReport,
)
from ai.interview.talent.general import (
    GeneralInterview,
    analyze_general_interview,
    analyze_general_interview_for_card,
)
from ai.interview.talent.technical import (
    TechnicalInterview,
    analyze_technical_interview_for_card,
)
from ai.interview.talent.situational import (
    SituationalInterview,
    analyze_situational_interview_for_card,
)
from ai.interview.talent.card_generator import (
    generate_candidate_profile_card,
    convert_card_to_backend_format,
)

__all__ = [
    # Models
    "GeneralInterviewAnalysis",
    "CandidateProfile",
    "CandidateProfileCard",
    "PersonaScores",
    "FinalPersonaReport",
    # General
    "GeneralInterview",
    "analyze_general_interview",
    # Technical
    "TechnicalInterview",
    # Situational
    "SituationalInterview",
    # Card Generator
    "generate_candidate_profile_card",
    "analyze_general_interview_for_card",
    "analyze_technical_interview_for_card",
    "analyze_situational_interview_for_card",
    "convert_card_to_backend_format",
]
