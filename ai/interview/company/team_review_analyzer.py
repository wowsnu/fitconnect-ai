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
    TeamCultureProfile,
    TeamReviewQuestions
)
from config.settings import get_settings


def _escape_curly(text: str) -> str:
    """LangChain 프롬프트에서 중괄호 이스케이프"""
    if not text:
        return ""
    return text.replace("{", "{{").replace("}", "}}")


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


def generate_team_review_questions(
    general_analysis: CompanyGeneralAnalysis,
    company_info: dict = None,
    existing_jd: dict = None
) -> TeamReviewQuestions:
    """
    팀원 리뷰용 직무적합성/문화적합성 질문 생성

    General 분석 결과, 기업 프로필, 기존 JD를 기반으로
    직무적합성 질문 2개, 문화적합성 질문 2개를 생성

    Args:
        general_analysis: General 면접 분석 결과
        company_info: 기업 프로필 (culture, vision_mission, business_domains 등)
        existing_jd: 기존 Job Description dict (responsibilities, requirements_must 등)

    Returns:
        TeamReviewQuestions (job_fit_questions 2개, culture_fit_questions 2개)
    """
    print("[TeamReview] Generating team review questions...")

    # 1. General 분석 결과 요약
    general_summary = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}
- 업무 방식: {general_analysis.work_style}
- 채용 이유: {general_analysis.hiring_reason}
"""

    # 2. 기업 프로필 컨텍스트
    company_context = ""
    if company_info:
        company_parts = []
        about = company_info.get("about", {})
        if about.get("culture"):
            company_parts.append(f"- 조직 문화: {about['culture']}")
        if about.get("vision_mission"):
            company_parts.append(f"- 비전/미션: {about['vision_mission']}")
        if about.get("business_domains"):
            company_parts.append(f"- 사업 영역: {about['business_domains']}")

        basic = company_info.get("basic", {})
        if basic.get("name"):
            company_parts.insert(0, f"- 회사명: {basic['name']}")
        if basic.get("industry"):
            company_parts.append(f"- 산업: {basic['industry']}")

        if company_parts:
            company_context = "\n[기업 프로필]\n" + "\n".join(company_parts) + "\n"

    # 3. 기존 JD 컨텍스트
    jd_context = ""
    if existing_jd:
        jd_parts = []
        if existing_jd.get("title"):
            jd_parts.append(f"- 포지션: {existing_jd['title']}")
        if existing_jd.get("position"):
            jd_parts.append(f"- 직무: {existing_jd['position']}")
        if existing_jd.get("department"):
            jd_parts.append(f"- 부서: {existing_jd['department']}")
        if existing_jd.get("responsibilities"):
            jd_parts.append(f"- 주요 업무:\n{existing_jd['responsibilities']}")
        if existing_jd.get("requirements_must"):
            jd_parts.append(f"- 필수 요건:\n{existing_jd['requirements_must']}")
        if existing_jd.get("requirements_nice"):
            jd_parts.append(f"- 우대 요건:\n{existing_jd['requirements_nice']}")

        if jd_parts:
            jd_context = "\n[기존 Job Description]\n" + "\n".join(jd_parts) + "\n"

    # 이스케이프 처리
    general_summary_safe = _escape_curly(general_summary)
    company_context_safe = _escape_curly(company_context)
    jd_context_safe = _escape_curly(jd_context)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 담당자입니다. 팀원들에게 직무적합성과 문화적합성에 대한 의견을 수집하기 위한 질문을 생성합니다.

**목표:**
General 면접 분석 결과, 기업 프로필, 기존 JD를 참고하여 팀원들이 각자의 관점에서 구체적으로 답변할 수 있는 질문을 생성합니다.

**직무적합성 질문 (2개) - job_fit_questions:**
- 해당 포지션에서 필요한 역량, 경험, 기술 스택에 대해 팀원 관점에서 구체적으로 물어보는 질문
- 실제 업무에서 어떤 역할을 기대하는지, 어떤 도전 과제가 있는지 파악하는 질문
- 기존 JD가 있다면 그 내용을 구체화하거나 보완할 수 있는 질문

**문화적합성 질문 (2개) - culture_fit_questions:**
- 팀의 협업 방식, 의사소통 스타일, 업무 환경에 대해 팀원 관점에서 물어보는 질문
- 어떤 성향의 사람이 팀에 잘 맞는지, 팀 문화의 특징을 파악하는 질문
- General 분석에서 나온 팀 문화를 더 구체화할 수 있는 질문

**질문 작성 원칙:**
- 모든 질문은 한글로 작성
- 열린 질문으로 작성 (예/아니오로 답할 수 없는 질문)
- 팀원 개인의 경험과 관점을 물어보는 형태
- 구체적이고 실무 중심의 질문
- 각 질문은 100자 이내로 간결하게 작성
- 질문마다 목적(purpose)을 명확히 기술

**질문 예시:**
- 직무적합성: "이 포지션에서 가장 중요하게 생각하는 기술 역량은 무엇이며, 어느 정도 수준을 기대하시나요?"
- 직무적합성: "신규 입사자가 처음 3개월간 수행하게 될 주요 업무는 무엇인가요?"
- 문화적합성: "팀에서 업무 진행 시 주로 어떤 방식으로 소통하고 협업하나요?"
- 문화적합성: "팀에 새로 합류하는 분에게 가장 필요한 성향이나 태도는 무엇이라고 생각하시나요?"
"""),
        ("user", f"""{general_summary_safe}
{company_context_safe}{jd_context_safe}
위 정보를 바탕으로 팀원 리뷰용 질문을 생성해주세요.
- 직무적합성 질문 2개
- 문화적합성 질문 2개
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TeamReviewQuestions)

    result = (prompt | llm).invoke({})

    print(f"[TeamReview] Generated {len(result.job_fit_questions)} job fit questions, {len(result.culture_fit_questions)} culture fit questions")

    return result
