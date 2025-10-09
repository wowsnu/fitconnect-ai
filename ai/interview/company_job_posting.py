"""
Company Job Posting Card Generator

3단계 면접 분석 결과를 통합하여 최종 채용 공고 카드 생성
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.company_models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile,
    JobPostingCard,
    CompanyInfo
)
from config.settings import get_settings


def generate_job_posting_card(
    company_name: str,
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    situational_profile: TeamCultureProfile,
    existing_jd: Optional[str] = None,
    deadline: Optional[str] = None
) -> JobPostingCard:
    """
    최종 채용 공고 카드 생성

    Args:
        company_name: 회사명
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        situational_profile: Situational 면접 분석 결과
        existing_jd: 기존 Job Description (선택, 기본 정보 추출용)
        deadline: 마감일 (선택)

    Returns:
        JobPostingCard
    """

    # 컨텍스트 구성
    context = f"""
[회사 정보]
회사명: {company_name}

[General 면접 분석 - 회사 문화 & 가치]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}
- 업무 방식: {general_analysis.work_style}
- 채용 이유: {general_analysis.hiring_reason}

[Technical 면접 분석 - 직무 정보]
- 직무명: {technical_requirements.job_title}
- 주요 업무: {', '.join(technical_requirements.main_responsibilities)}
- 필수 역량: {', '.join(technical_requirements.required_skills)}
- 우대 역량: {', '.join(technical_requirements.preferred_skills)}
- 예상 도전: {technical_requirements.expected_challenges}

[Situational 면접 분석 - 팀 문화]
- 팀 현황: {situational_profile.team_situation}
- 협업 스타일: {situational_profile.collaboration_style}
- 갈등 해결: {situational_profile.conflict_resolution}
- 업무 환경: {situational_profile.work_environment}
- 선호 스타일: {situational_profile.preferred_work_style}
"""

    # 기존 JD가 있으면 추가
    jd_context = ""
    if existing_jd:
        jd_context = f"\n[기존 Job Description - 기본 정보 참고용]\n{existing_jd}\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 전문가입니다.

3단계 면접 분석 결과를 통합하여, 매력적인 채용 공고 카드를 생성하세요.

**생성 규칙:**

1. **기본 공고 정보** (experience_level, contract_duration, department, employment_type, salary_info):
   - 기존 JD가 있으면 거기서 추출
   - 없으면 면접 내용에서 추론 (예: "3-5년차 경력직", "개발팀")

2. **주요 역할/업무** (main_responsibilities):
   - Technical 분석 결과에서 **정확히 4개** 추출
   - 구체적이고 명확하게

3. **자격 요건** (required_skills):
   - Technical 분석의 필수 역량에서 **정확히 4개**

4. **요구 역량** (preferred_skills):
   - Technical 분석의 우대 역량에서 **정확히 4개**

5. **기업 정보** (company_info):
   - funding_stage: 기존 JD에서 추출 (없으면 null)
   - company_culture: General 분석의 team_culture + work_style 통합 (2-3문장)
   - benefits: 면접 내용에서 언급된 복리후생 (없으면 빈 리스트)

6. **인재상** (personality_fit):
   - General의 ideal_candidate_traits + Situational 분석 통합
   - 2-3문장으로 정리

7. **도전 과제** (challenges):
   - Technical의 expected_challenges 활용
   - 긍정적으로 재구성 (성장 기회 강조)

**중요:**
- main_responsibilities, required_skills, preferred_skills는 **반드시 정확히 4개씩**
- 실제 분석 결과에 있는 내용만 사용
- 추측하거나 과장하지 말 것
- 일관성 있고 매력적인 공고로 작성
"""),
        ("user", f"{context}{jd_context}")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.4,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(JobPostingCard)

    result = (prompt | llm).invoke({})

    # 회사명과 마감일 덮어쓰기
    result.company_name = company_name
    if deadline:
        result.deadline = deadline

    return result


def extract_basic_info_from_jd(jd_text: str) -> dict:
    """
    기업 프로필 db에서 정보 가져오기. 추후 수정

    Args:
        jd_text: Job Description 텍스트

    Returns:
        dict with keys: experience_level, contract_duration, department,
                        employment_type, salary_info, funding_stage
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 Job Description 분석 전문가입니다.

기존 JD에서 다음 기본 정보만 추출하세요:

1. **experience_level**: 경력 요구사항 (예: "신입", "경력 3-5년", "시니어")
2. **contract_duration**: 근무 기간 (예: "정규직", "6개월", "1년 계약직")
3. **department**: 부서명 (예: "개발팀", "마케팅팀")
4. **employment_type**: 고용 형태 (예: "정규직", "계약직", "인턴")
5. **salary_info**: 연봉 정보 (예: "4000-6000만원", "협상 가능")
6. **funding_stage**: 투자 단계 (예: "Series A", "Pre-IPO")

**중요:**
- JD에 명시된 내용만 추출
- 없는 정보는 null로 반환
- 추측하지 말 것
"""),
        ("user", jd_text)
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY
    )

    # 단순 dict 반환
    response = (prompt | llm).invoke({})

    # 응답 파싱 (간단한 dict 형태로)
    # 실제로는 structured output 사용 권장하지만, 여기선 간단히 처리
    return {
        "experience_level": None,
        "contract_duration": None,
        "department": None,
        "employment_type": None,
        "salary_info": None,
        "funding_stage": None,
        # TODO: 실제 파싱 로직 구현 또는 structured output 사용
    }
