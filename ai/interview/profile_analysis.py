"""
Profile Analysis (프로필 카드 생성)

3가지 면접 결과를 종합하여 지원자 프로필 분석 카드 생성
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.models import (
    CandidateProfileCard,
    GeneralInterviewAnalysis,
    FinalPersonaReport,
    CandidateProfile
)
from config.settings import get_settings


def generate_candidate_profile_card(
    candidate_profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    technical_results: dict,
    situational_report: FinalPersonaReport
) -> CandidateProfileCard:
    """
    3가지 면접 분석 결과를 종합하여 프로필 카드 생성

    Args:
        candidate_profile: 지원자 기본 프로필
        general_analysis: 일반 면접 분석 결과
        technical_results: 기술 면접 결과 (평가된 기술 목록)
        situational_report: 상황 면접 페르소나 리포트

    Returns:
        CandidateProfileCard
    """
    # 기술 면접에서 평가된 스킬 요약
    evaluated_skills = technical_results.get("skills_evaluated", []) if technical_results else []
    skills_summary = ", ".join(evaluated_skills) if evaluated_skills else ", ".join(candidate_profile.skills[:3])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 전문가입니다.
지원자의 면접 결과를 종합 분석하여 **프로필 카드**를 작성하세요.

**작성 가이드:**

1. **주요 경험/경력** (4개):
   - 구체적인 프로젝트나 업무 경험
   - "마이크로서비스 아키텍처 설계 및 구축"
   - "신규 AI 면접 시스템 개발 리드"

2. **강점** (4개):
   - 업무 수행 시 돋보이는 강점
   - "빠른 학습 능력과 기술 습득력"
   - "체계적인 문제 해결 접근"

3. **핵심 일반 역량** (4개):
   - Soft skills (리더십, 커뮤니케이션, 협업 등)
   - 각 역량의 수준: "높음", "보통", "낮음"
   - 예: {{"name": "리더십", "level": "높음"}}

4. **핵심 직무 역량/기술** (4개):
   - Hard skills (기술 스택, 전문 지식 등)
   - 각 역량의 수준: "높음", "보통", "낮음"
   - 예: {{"name": "Python/FastAPI", "level": "높음"}}

5. **직무 성향**: 한 문장으로 요약
6. **협업 성향**: 한 문장으로 요약
7. **성장 가능성**: 한 문장으로 요약

**주의:**
- 실제 면접 내용에 근거하여 작성
- 추측하지 말고 드러난 내용만 작성
- 구체적이고 명확하게 작성
"""),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 직무: {candidate_profile.basic.tagline if candidate_profile.basic else "개발자"}
- 총 경력: {sum(exp.duration_years for exp in candidate_profile.experiences)}년

## 경력사항
{chr(10).join([f"- {exp.company_name} / {exp.title} ({exp.duration_years}년)" for exp in candidate_profile.experiences]) if candidate_profile.experiences else "정보 없음"}

## 학력
{chr(10).join([f"- {edu.school_name} / {edu.major or ''} ({edu.status})" for edu in candidate_profile.educations]) if candidate_profile.educations else "정보 없음"}

## 활동/프로젝트
{chr(10).join([f"- {act.name} ({act.category})" for act in candidate_profile.activities]) if candidate_profile.activities else "정보 없음"}

## 자격증
{chr(10).join([f"- {cert.name}" for cert in candidate_profile.certifications]) if candidate_profile.certifications else "정보 없음"}

## 구조화 면접 분석 결과
- 주요 테마: {', '.join(general_analysis.key_themes)}
- 관심사: {', '.join(general_analysis.interests)}
- 업무 스타일: {', '.join(general_analysis.work_style_hints)}
- 강조한 경험: {', '.join(general_analysis.emphasized_experiences)}
- 기술 키워드: {', '.join(general_analysis.technical_keywords)}

## 기술 면접 분석 결과
- 평가된 기술: {skills_summary}

## 상황 면접 페르소나 분석
- 업무 스타일: {situational_report.work_style}
- 문제 해결: {situational_report.problem_solving}
- 학습 성향: {situational_report.learning}
- 스트레스 대응: {situational_report.stress_response}
- 커뮤니케이션: {situational_report.communication}
- 종합 요약: {situational_report.summary}
- 팀 적합도: {situational_report.team_fit}

위 분석 결과를 바탕으로 프로필 카드를 작성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(CandidateProfileCard)

    # 기본 정보 병합
    result = (prompt | llm).invoke({})

    # 기본 프로필 정보는 확정값 사용
    result.candidate_name = candidate_profile.basic.name if candidate_profile.basic else "지원자"
    result.role = candidate_profile.basic.tagline if candidate_profile.basic else "개발자"
    result.experience_years = sum(exp.duration_years for exp in candidate_profile.experiences)
    result.company = candidate_profile.experiences[0].company_name if candidate_profile.experiences else ""

    return result
