"""
기업 면접 결과 → 채용공고(JD) 생성
Company Interview Analysis to Job Posting Generator
"""

from typing import Optional, List, Dict, Any
from ai.interview.company_models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile
)


def create_job_posting_from_interview(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    team_fit_analysis: TeamCultureProfile
) -> Dict[str, Any]:
    """
    면접 분석 결과를 채용공고 데이터로 변환

    Args:
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        team_fit_analysis: Situational 면접 분석 결과

    Returns:
        채용공고 POST 요청에 필요한 dict (선택적 필드만 포함)
    """
    job_posting = {}

    # 필수 필드들
    if technical_requirements.job_title:
        job_posting["title"] = technical_requirements.job_title

    # 주요 업무 (List[str] -> str 변환)
    if technical_requirements.main_responsibilities:
        responsibilities_text = "\n".join([f"- {r}" for r in technical_requirements.main_responsibilities])
        job_posting["responsibilities"] = responsibilities_text

    # 필수 요건 (List[str] -> str 변환)
    if technical_requirements.required_skills:
        requirements_text = "\n".join([f"- {s}" for s in technical_requirements.required_skills])
        job_posting["requirements_must"] = requirements_text

    # 우대 요건 (List[str] -> str 변환)
    if technical_requirements.preferred_skills:
        preferred_text = "\n".join([f"- {s}" for s in technical_requirements.preferred_skills])
        job_posting["requirements_nice"] = preferred_text

    # 필요 역량 (리스트 형태 - 그대로 사용)
    if technical_requirements.required_skills:
        job_posting["competencies"] = technical_requirements.required_skills[:10]

    # 필수 필드들 (공백으로 전송)
    job_posting["location_city"] = ""
    job_posting["career_level"] = ""
    job_posting["education_level"] = ""
    job_posting["employment_type"] = ""
    job_posting["status"] = "DRAFT"

    return job_posting
