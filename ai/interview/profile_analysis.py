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
    CandidateProfile,
    GeneralInterviewCardPart,
    TechnicalInterviewCardPart,
    SituationalInterviewCardPart,
    CompetencyItem
)
from config.settings import get_settings


def convert_card_to_backend_format(
    card: CandidateProfileCard,
    candidate_profile: CandidateProfile
) -> dict:
    """
    CandidateProfileCard를 백엔드 API 형식으로 변환

    Args:
        card: 생성된 프로필 카드
        candidate_profile: 지원자 기본 프로필

    Returns:
        백엔드 API에 보낼 dict
    """
    # Level 매핑: "높음" -> "high", "보통" -> "medium", "낮음" -> "low"
    level_mapping = {
        "높음": "high",
        "보통": "medium",
        "낮음": "low"
    }

    # 가장 최신 경력 찾기 (end_ym이 없거나 가장 늦은 경력)
    current_employment = ""
    current_years = 0

    if candidate_profile.experiences:
        # end_ym이 없는 경력 찾기 (현재 재직 중)
        current_job = next((exp for exp in candidate_profile.experiences if not exp.end_ym), None)

        # 없으면 가장 최근 경력
        if not current_job:
            current_job = candidate_profile.experiences[0]

        current_employment = current_job.company_name
        current_years = current_job.duration_years or 0

    # headline 생성: "안녕하세요, {tagline} 입니다."
    tagline = ""
    if candidate_profile.basic and candidate_profile.basic.tagline:
        tagline = candidate_profile.basic.tagline
    elif card.role:
        tagline = card.role
    else:
        # 경력이 있으면 최근 직무명 사용
        if candidate_profile.experiences:
            tagline = candidate_profile.experiences[0].title
        else:
            tagline = "개발자"

    headline = f"안녕하세요, {tagline} 입니다."

    # badge_title도 동일하게 처리
    badge_title = card.role if card.role else tagline

    return {
        "header_title": card.candidate_name,
        "badge_title": badge_title,
        "badge_years": current_years,
        "badge_employment": current_employment if current_employment else None,
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
        "user_id": candidate_profile.basic.user_id if candidate_profile.basic else 0
    }


def analyze_general_interview(
    candidate_profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    answers: list[dict]
) -> GeneralInterviewCardPart:
    """
    구조화 면접 결과 분석 - 주요 경험/경력 (1) + 핵심 일반 역량 (3)

    Args:
        candidate_profile: 지원자 기본 프로필
        general_analysis: 구조화 면접 분석 결과 (직무면접 개인화용)
        answers: 원본 Q&A [{"question": str, "answer": str}, ...] 

    Returns:
        GeneralInterviewCardPart (key_experiences, core_competencies)
    """
    # 원본 Q&A를 텍스트로 결합
    all_qa = "\n\n".join([
        f"질문: {a['question']}\n답변: {a['answer']}"
        for a in answers
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 전문가입니다.
구조화 면접 결과를 분석하여 **주요 경험/경력**과 **핵심 일반 역량**을 추출하세요.

**추출 목표:**

1. **주요 경험/경력 (4개)**:
   - 구체적인 프로젝트나 업무 경험
   - 면접에서 강조한 경험 위주
   - 예: "마이크로서비스 아키텍처 설계 및 구축", "신규 결제 시스템 개발 리드"

2. **핵심 일반 역량 (4개)**:
   - Soft skills (리더십, 커뮤니케이션, 협업, 문제해결 등)
   - 각 역량의 수준: "높음", "보통", "낮음"
   - 면접에서 드러난 업무 스타일과 태도 기반
   - 예: {{"name": "협업 능력", "level": "높음"}}

**레벨 판단 기준:**
- **높음**: 구체적 사례와 함께 여러 번 강조, 명확한 성과 제시
- **보통**: 언급은 되었으나 깊이가 부족하거나 1-2회 언급
- **낮음**: 거의 언급 안됨 또는 매우 피상적

**주의:**
- 실제 면접 답변에 근거하여 작성
- 추측하지 말고 드러난 내용만 추출
- 구체적이고 명확하게 작성
"""),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 직무: {candidate_profile.basic.tagline if candidate_profile.basic else "개발자"}
- 총 경력: {sum((exp.duration_years or 0) for exp in candidate_profile.experiences)}년

## 경력사항
{chr(10).join([f"- {exp.company_name} / {exp.title} ({exp.duration_years or 0}년)" for exp in candidate_profile.experiences]) if candidate_profile.experiences else "정보 없음"}

## 구조화 면접 분석 결과 (참고용)
- 주요 테마: {', '.join(general_analysis.key_themes)}
- 관심사: {', '.join(general_analysis.interests)}
- 업무 스타일: {', '.join(general_analysis.work_style_hints)}
- 강조한 경험: {', '.join(general_analysis.emphasized_experiences)}
- 기술 키워드: {', '.join(general_analysis.technical_keywords)}

## 구조화 면접 원본 답변
{all_qa}

위 정보를 바탕으로 **주요 경험/경력 4개**와 **핵심 일반 역량 4개**(레벨 포함)를 추출하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(GeneralInterviewCardPart)

    return (prompt | llm).invoke({})


def analyze_technical_interview(
    candidate_profile: CandidateProfile,
    technical_results: dict
) -> TechnicalInterviewCardPart:
    """
    직무적합성 면접 결과 분석 - 강점 (2) + 핵심 직무 역량/기술 (4)

    Args:
        candidate_profile: 지원자 기본 프로필
        technical_results: 직무적합성 면접 결과

    Returns:
        TechnicalInterviewCardPart (strengths, technical_skills)
    """
    # 기술 면접 결과에서 질문/답변 추출
    skills_evaluated = technical_results.get("skills_evaluated", [])
    results = technical_results.get("results", {})

    # 모든 질문과 답변을 텍스트로 정리
    qa_summary = []
    for skill, questions in results.items():
        qa_summary.append(f"\n[{skill}]")
        for q in questions:
            qa_summary.append(f"Q: {q['question'][:100]}...")
            qa_summary.append(f"A: {q['answer'][:150]}...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 전문가입니다.
직무적합성 면접 결과를 분석하여 **강점**과 **핵심 직무 역량/기술**을 추출하세요.

**추출 목표:**

1. **강점 (4개)**:
   - 업무 수행 시 돋보이는 강점
   - 기술 면접에서 드러난 실력과 경험
   - 예: "빠른 학습 능력과 기술 습득력", "체계적인 문제 해결 접근", "성능 최적화 전문성"

2. **핵심 직무 역량/기술 (4개)**:
   - Hard skills (기술 스택, 전문 지식 등)
   - 각 역량의 수준: "높음", "보통", "낮음"
   - 실제 사용 경험과 깊이 기반
   - 예: {{"name": "Python/FastAPI", "level": "높음"}}, {{"name": "데이터베이스 최적화", "level": "보통"}}

**레벨 판단 기준:**
- **높음**: 깊이 있는 이해, 최적화/트러블슈팅 경험, 구체적 수치나 성과 제시
- **보통**: 기본적 사용 경험, 간단한 구현 가능, 일부 경험 있음
- **낮음**: 개념만 알거나 매우 제한적 경험

**주의:**
- 실제 면접 답변에 근거하여 작성
- 답변의 깊이와 구체성으로 수준 판단
- 추측하지 말고 드러난 내용만 추출
"""),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 직무: {candidate_profile.basic.tagline if candidate_profile.basic else "개발자"}
- 기술 스택: {', '.join([exp.summary or '' for exp in candidate_profile.experiences if exp.summary])}

## 직무적합성 면접 결과
- 평가된 기술: {', '.join(skills_evaluated)}

## 질문/답변 요약
{chr(10).join(qa_summary)}

위 정보를 바탕으로 **강점 4개**와 **핵심 직무 역량/기술 4개**를 추출하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TechnicalInterviewCardPart)

    return (prompt | llm).invoke({})


def analyze_situational_interview(
    candidate_profile: CandidateProfile,
    situational_report: FinalPersonaReport,
    qa_history: list[dict],
    general_part: GeneralInterviewCardPart,
    technical_part: TechnicalInterviewCardPart
) -> SituationalInterviewCardPart:
    """
    상황 면접 결과 분석 - 직무적합성 (5) + 협업성향 (6) + 성장가능성 (7) + 부족한 부분 보완

    Args:
        candidate_profile: 지원자 기본 프로필
        situational_report: 상황 면접 페르소나 리포트
        qa_history: 상황 면접 원본 Q&A (보완 정보 추출용)
        general_part: 구조화 면접 카드 (부족한 부분 확인용)
        technical_part: 직무적합성 면접 카드 (부족한 부분 확인용)

    Returns:
        SituationalInterviewCardPart (job_fit, team_fit, growth_potential + 보완)
    """
    # 원본 Q&A를 텍스트로 결합
    qa_text = "\n\n".join([
        f"질문: {qa['question']}\n답변: {qa['answer'][:150]}..."
        for qa in qa_history
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 전문가입니다.
상황 면접 결과를 분석하여 **직무 적합성**, **협업 성향**, **성장 가능성**을 요약하세요.
또한 이전 면접에서 부족한 부분이 있다면 보완하세요.

**추출 목표:**

1. **직무 적합성** (한 문장):
   - 페르소나와 업무 스타일을 종합하여 직무 적합도 평가
   - 예: "체계적이고 논리적인 문제 해결로 백엔드 개발에 적합"

2. **협업 성향** (한 문장):
   - 커뮤니케이션과 팀워크 스타일 요약
   - 예: "적극적인 코드 리뷰와 지식 공유로 팀 성장에 기여"

3. **성장 가능성** (한 문장):
   - 학습 성향과 발전 가능성 평가
   - 예: "빠른 학습 능력과 실험적 태도로 신기술 습득에 강점"

4. **부족한 부분 보완** (Optional):
   - 이전 면접에서 충분히 드러나지 않은 경험, 강점, 역량이 있다면 추가
   - 상황 면접 답변에서 새로 발견된 내용 위주

**주의:**
- 각 항목은 한 문장으로 명확하게 작성
- 페르소나 분석 결과와 일관성 유지
- 보완 항목은 실제로 필요한 경우에만 추가
"""),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 직무: {candidate_profile.basic.tagline if candidate_profile.basic else "개발자"}

## 상황 면접 페르소나 분석
- 업무 스타일: {situational_report.work_style}
- 문제 해결: {situational_report.problem_solving}
- 학습 성향: {situational_report.learning}
- 스트레스 대응: {situational_report.stress_response}
- 커뮤니케이션: {situational_report.communication}
- 종합 요약: {situational_report.summary}
- 팀 적합도: {situational_report.team_fit}

## 상황 면접 원본 답변
{qa_text}

## 이전 면접 결과 (부족한 부분 확인용)
- 추출된 주요 경험: {len(general_part.key_experiences)}개
- 추출된 일반 역량: {len(general_part.core_competencies)}개
- 추출된 강점: {len(technical_part.strengths)}개
- 추출된 직무 역량: {len(technical_part.technical_skills)}개

위 정보를 바탕으로:
1. **직무 적합성** 한 문장
2. **협업 성향** 한 문장
3. **성장 가능성** 한 문장
4. 상황 면접 답변에서 이전 면접에서 다루지 못한 경험/강점/역량이 있다면 보완 (없으면 빈 리스트)
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(SituationalInterviewCardPart)

    return (prompt | llm).invoke({})


def generate_candidate_profile_card(
    candidate_profile: CandidateProfile,
    general_part: GeneralInterviewCardPart,
    technical_part: TechnicalInterviewCardPart,
    situational_part: SituationalInterviewCardPart
) -> CandidateProfileCard:
    """
    3가지 면접의 부분 카드를 통합하여 최종 프로필 카드 생성

    Args:
        candidate_profile: 지원자 기본 프로필
        general_part: 구조화 면접 카드 (경험/경력 + 일반 역량)
        technical_part: 직무적합성 면접 카드 (강점 + 직무 역량)
        situational_part: 상황 면접 카드 (직무적합성 + 협업 + 성장 + 보완)

    Returns:
        CandidateProfileCard (7가지 항목 모두 포함)
    """
    # 기본 정보
    candidate_name = candidate_profile.basic.name if candidate_profile.basic else "지원자"

    # role 결정: tagline → 최근 직무명 → "개발자"
    role = ""
    if candidate_profile.basic and candidate_profile.basic.tagline:
        role = candidate_profile.basic.tagline
    elif candidate_profile.experiences:
        role = candidate_profile.experiences[0].title
    else:
        role = "개발자"

    experience_years = sum((exp.duration_years or 0) for exp in candidate_profile.experiences)
    company = candidate_profile.experiences[0].company_name if candidate_profile.experiences else ""

    # 1. 주요 경험/경력 (구조화 면접 + 상황 면접 보완)
    key_experiences = general_part.key_experiences + situational_part.additional_experiences
    key_experiences = key_experiences[:4]  # 최대 4개

    # 2. 강점 (직무적합성 면접 + 상황 면접 보완)
    strengths = technical_part.strengths + situational_part.additional_strengths
    strengths = strengths[:4]  # 최대 4개

    # 3. 핵심 일반 역량 (구조화 면접 + 상황 면접 보완)
    core_competencies = general_part.core_competencies + situational_part.additional_competencies
    core_competencies = core_competencies[:4]  # 최대 4개

    # 4. 핵심 직무 역량/기술 (직무적합성 면접 + 상황 면접 보완)
    technical_skills = technical_part.technical_skills + situational_part.additional_technical
    technical_skills = technical_skills[:4]  # 최대 4개

    # 5, 6, 7. 직무적합성, 협업성향, 성장가능성 (상황 면접)
    job_fit = situational_part.job_fit
    team_fit = situational_part.team_fit
    growth_potential = situational_part.growth_potential

    # 최종 카드 생성
    return CandidateProfileCard(
        candidate_name=candidate_name,
        role=role,
        experience_years=experience_years,
        company=company,
        key_experiences=key_experiences,
        strengths=strengths,
        core_competencies=core_competencies,
        technical_skills=technical_skills,
        job_fit=job_fit,
        team_fit=team_fit,
        growth_potential=growth_potential
    )
