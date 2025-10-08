"""
AI Interview System

3가지 인터뷰 타입:
1. General Interview (구조화 면접) - 고정 질문 5-7개
2. Technical Interview (직무 적합성 면접) - 3개 기술 × 3단계 = 9개 질문
3. Situational Interview (상황 면접) - 페르소나 분석 6개 질문
"""

from ai.interview.models import (
    GeneralInterviewAnalysis,
    CandidateProfile,
    InterviewQuestion,
    AnswerFeedback,
    PersonaDimensions,
    PersonaScores,
)

__all__ = [
    "GeneralInterviewAnalysis",
    "CandidateProfile",
    "InterviewQuestion",
    "AnswerFeedback",
    "PersonaDimensions",
    "PersonaScores",
]
