"""
Candidate Card Generator (인재 카드 생성)

3가지 면접 결과를 종합하여 지원자 프로필 카드 생성
- General, Technical, Situational 분석 결과 통합
- 백엔드 API 형식으로 변환
"""

from ai.interview.talent.models import (
    CandidateProfile,
    CandidateProfileCard,
    GeneralInterviewCardPart,
    TechnicalInterviewCardPart,
    SituationalInterviewCardPart,
)


def convert_card_to_backend_format(
    card: CandidateProfileCard,
    candidate_profile: CandidateProfile,
) -> dict:
    """
    CandidateProfileCard를 백엔드 API 형식으로 변환
    """
    level_mapping = {
        "높음": "high",
        "보통": "medium",
        "낮음": "low",
    }

    current_employment = ""
    current_years = 0
    if candidate_profile.experiences:
        current_job = next(
            (exp for exp in candidate_profile.experiences if not exp.end_ym), None
        )
        if not current_job:
            current_job = candidate_profile.experiences[0]

        current_employment = current_job.company_name
        current_years = current_job.duration_years or 0

    if candidate_profile.basic and candidate_profile.basic.tagline:
        tagline = candidate_profile.basic.tagline
    elif card.role:
        tagline = card.role
    elif candidate_profile.experiences:
        tagline = candidate_profile.experiences[0].title
    else:
        tagline = "개발자"

    headline = f"안녕하세요, {tagline} 입니다."
    badge_title = card.role if card.role else tagline

    return {
        "header_title": card.candidate_name,
        "badge_title": badge_title,
        "badge_years": current_years,
        "badge_employment": current_employment or None,
        "headline": headline,
        "experiences": card.key_experiences,
        "strengths": card.strengths,
        "general_capabilities": [
            {"name": comp.name, "level": level_mapping.get(comp.level, "medium")}
            for comp in card.core_competencies
        ],
        "job_skills": [
            {"name": skill.name, "level": level_mapping.get(skill.level, "medium")}
            for skill in card.technical_skills
        ],
        "performance_summary": card.job_fit,
        "collaboration_style": card.team_fit,
        "growth_potential": card.growth_potential,
        "user_id": candidate_profile.basic.user_id if candidate_profile.basic else 0,
    }


def generate_candidate_profile_card(
    candidate_profile: CandidateProfile,
    general_part: GeneralInterviewCardPart,
    technical_part: TechnicalInterviewCardPart,
    situational_part: SituationalInterviewCardPart,
) -> CandidateProfileCard:
    """
    3가지 면접 파트를 통합하여 최종 프로필 카드 생성
    """
    candidate_name = candidate_profile.basic.name if candidate_profile.basic else "지원자"

    if candidate_profile.basic and candidate_profile.basic.tagline:
        role = candidate_profile.basic.tagline
    elif candidate_profile.experiences:
        role = candidate_profile.experiences[0].title
    else:
        role = "개발자"

    experience_years = sum((exp.duration_years or 0) for exp in candidate_profile.experiences)
    company = candidate_profile.experiences[0].company_name if candidate_profile.experiences else ""

    key_experiences = (general_part.key_experiences + situational_part.additional_experiences)[:4]
    strengths = (technical_part.strengths + situational_part.additional_strengths)[:4]
    core_competencies = (
        general_part.core_competencies + situational_part.additional_competencies
    )[:4]
    technical_skills = (
        technical_part.technical_skills + situational_part.additional_technical
    )[:4]

    return CandidateProfileCard(
        candidate_name=candidate_name,
        role=role,
        experience_years=experience_years,
        company=company,
        key_experiences=key_experiences,
        strengths=strengths,
        core_competencies=core_competencies,
        technical_skills=technical_skills,
        job_fit=situational_part.job_fit,
        team_fit=situational_part.team_fit,
        growth_potential=situational_part.growth_potential,
    )
