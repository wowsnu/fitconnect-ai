"""
Company Team Review Analyzer (팀원 리뷰 분석)

여러 팀원의 직무적합성/문화적합성 답변을 종합 분석하여
기존 TechnicalRequirements, TeamCultureProfile 형식으로 변환
"""

from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.company.models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile
)
from config.settings import get_settings


def analyze_team_review_technical(
    member_reviews: List[Dict[str, str]],
    general_analysis: CompanyGeneralAnalysis
) -> TechnicalRequirements:
    """
    여러 팀원의 직무적합성 답변을 종합 분석

    Args:
        member_reviews: [{"member_name": "김철수", "role": "시니어 개발자", "job_fit_answer": "..."}, ...]
        general_analysis: General 면접 분석 결과

    Returns:
        TechnicalRequirements
    """
    # 모든 팀원 답변을 하나의 컨텍스트로 구성
    all_member_answers = "\n\n".join([
        f"=== 팀원 {i+1}: {m['member_name']} ({m['role']}) ===\n{m['job_fit_answer']}"
        for i, m in enumerate(member_reviews)
    ])

    # General 분석 결과 요약
    general_summary = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 채용 이유: {general_analysis.hiring_reason}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 담당자입니다.

여러 팀원이 작성한 직무적합성 답변을 종합 분석하여, 채용 공고에 들어갈 직무 정보를 추출하세요.

**추출 목표:**
1. **job_title**: 직무명 (팀원들이 언급한 직무를 종합)
2. **main_responsibilities**: 주요 업무 (여러 팀원이 언급한 모든 업무를 구체적으로 나열)
3. **required_skills**: 필수 역량 (대다수 팀원이 강조한 역량, 명확한 수준 포함)
4. **preferred_skills**: 우대 역량 (일부 팀원이 언급한 역량)
5. **expected_challenges**: 예상되는 어려움/도전 과제 (팀원들이 언급한 어려움을 종합하여 2-3문장)

**종합 원칙:**
- 여러 팀원의 관점을 모두 고려하여 균형있게 반영
- **대다수(50% 이상) 팀원이 언급한 내용** → 필수 역량/주요 업무로 포함
- **일부 팀원만 언급한 내용** → 우대 역량으로 포함
- 팀원들 간 의견 차이가 있으면 포괄적으로 표현
- 실제 답변에 있는 내용만 사용 (추측하거나 과장하지 말 것)
- 각 팀원 답변의 맥락을 유지하면서 종합
- General 면접 결과와 일관성 유지

**중요:**
- 구체적이고 명확한 표현 사용
- required_skills, preferred_skills는 명확히 구분
- main_responsibilities는 실제 업무 중심으로 구체적으로
"""),
        ("user", f"""{general_summary}

[팀원들의 직무적합성 답변 (총 {len(member_reviews)}명)]
{all_member_answers}

위 {len(member_reviews)}명의 팀원 답변을 종합하여 TechnicalRequirements를 생성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TechnicalRequirements)

    return (prompt | llm).invoke({})


def analyze_team_review_culture(
    member_reviews: List[Dict[str, str]],
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements
) -> TeamCultureProfile:
    """
    여러 팀원의 문화적합성 답변을 종합 분석

    Args:
        member_reviews: [{"member_name": "김철수", "role": "시니어 개발자", "culture_fit_answer": "..."}, ...]
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과

    Returns:
        TeamCultureProfile
    """
    # 모든 팀원 답변을 하나의 컨텍스트로 구성
    all_member_answers = "\n\n".join([
        f"=== 팀원 {i+1}: {m['member_name']} ({m['role']}) ===\n{m['culture_fit_answer']}"
        for i, m in enumerate(member_reviews)
    ])

    # 이전 분석 결과 요약
    context = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}

[Technical 면접 분석 결과]
- 직무: {technical_requirements.job_title}
- 예상 도전: {technical_requirements.expected_challenges}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 담당자입니다.

여러 팀원이 작성한 문화적합성 답변을 종합 분석하여, 팀 문화와 적합한 인재상을 정의하세요.

**추출 목표:**
1. **team_situation**: 팀 현황 (성장기, 안정기 등) - 2-3문장으로 구체적으로 서술
2. **collaboration_style**: 선호하는 협업 스타일 - 2-3문장으로 구체적으로 서술
3. **conflict_resolution**: 갈등 해결 방식 - 2-3문장으로 구체적으로 서술
4. **work_environment**: 업무 환경 특성 - 2-3문장으로 구체적으로 서술
5. **preferred_work_style**: 선호하는 업무 스타일 - 2-3문장으로 구체적으로 서술

**종합 원칙:**
- 여러 팀원의 관점을 모두 고려하여 균형있게 반영
- 팀원들이 공통적으로 강조한 문화적 특성을 우선적으로 반영
- 팀원들 간 의견 차이가 있으면 포괄적으로 표현하되, 주된 의견을 중심으로
- 실제 답변에 있는 내용만 추출 (추측하거나 과장하지 말 것)
- 각 팀원 답변의 맥락을 유지하면서 종합
- General/Technical 결과와 일관성 유지

**중요:**
- 구체적이고 명확한 표현 사용
- 채용 공고의 "팀 문화" 및 "인재상" 섹션에 활용될 내용
- 팀의 실제 업무 방식과 문화를 솔직하게 반영
"""),
        ("user", f"""{context}

[팀원들의 문화적합성 답변 (총 {len(member_reviews)}명)]
{all_member_answers}

위 {len(member_reviews)}명의 팀원 답변을 종합하여 TeamCultureProfile을 생성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TeamCultureProfile)

    return (prompt | llm).invoke({})


def analyze_general_text_only(
    general_answer: str
) -> CompanyGeneralAnalysis:
    """
    구조화 질문 1개 텍스트 답변 분석 (팀원 리뷰용)

    Args:
        general_answer: 구조화 질문에 대한 긴 텍스트 답변

    Returns:
        CompanyGeneralAnalysis
    """
    # 기존 analyze_company_general_interview 함수 재사용
    from ai.interview.company.general import analyze_company_general_interview

    # 1개 질문-답변 쌍으로 변환
    answers = [{
        "question": "회사의 핵심 가치, 팀 문화, 이상적인 인재상, 채용 이유, 업무 방식을 종합적으로 말씀해주세요.",
        "answer": general_answer
    }]

    return analyze_company_general_interview(answers)
