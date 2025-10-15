"""
기업 면접 결과 → 채용공고(JD) 생성 및 카드 생성
Company Interview Analysis to Job Posting Generator
"""

from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ai.interview.company.models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile
)
from config.settings import get_settings


# JD 데이터 스키마 정의
class JobPostingData(BaseModel):
    """채용공고 데이터"""
    title: str = Field(description="직무명")
    responsibilities: List[str] = Field(description="주요 업무 (정확히 4개)", min_length=4, max_length=4)
    requirements_must: List[str] = Field(description="필수 요건 (정확히 4개)", min_length=4, max_length=4)
    requirements_nice: List[str] = Field(description="우대 요건 (정확히 4개)", min_length=4, max_length=4)
    competencies: List[str] = Field(description="요구 역량 (정확히 4개)", min_length=4, max_length=4)


def create_job_posting_from_interview(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    team_fit_analysis: TeamCultureProfile
) -> Dict[str, Any]:
    """
    면접 분석 결과를 LLM 기반 채용공고 데이터로 변환

    Args:
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        team_fit_analysis: Situational 면접 분석 결과

    Returns:
        채용공고 POST 요청에 필요한 dict
    """
    # 컨텍스트 구성 (모든 분석 결과 포함)
    context = f"""
[General 면접 분석 - 회사 문화 & 가치]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적인 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}
- 업무 방식: {general_analysis.work_style}
- 채용 이유: {general_analysis.hiring_reason}

[Technical 면접 분석 - 직무 정보]
- 직무명: {technical_requirements.job_title}
- 주요 업무: {', '.join(technical_requirements.main_responsibilities)}
- 필수 역량: {', '.join(technical_requirements.required_skills)}
- 우대 역량: {', '.join(technical_requirements.preferred_skills)}
- 예상 도전 과제: {technical_requirements.expected_challenges}

[Situational 면접 분석 - 팀 문화 & 협업]
- 팀 현황: {team_fit_analysis.team_situation}
- 협업 스타일: {team_fit_analysis.collaboration_style}
- 갈등 해결: {team_fit_analysis.conflict_resolution}
- 업무 환경: {team_fit_analysis.work_environment}
- 선호 업무 스타일: {team_fit_analysis.preferred_work_style}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 전문가입니다.

면접 분석 결과를 바탕으로 명확하고 구체적인 채용공고(JD)를 작성하세요.

**작성 규칙:**

1. **title**: 직무명 (Technical 분석의 job_title 사용)

2. **responsibilities**: 주요 업무
   - 리스트 형태로 반환
   - 구체적이고 명확하게 작성
   - 예: ["RESTful API 설계 및 개발", "데이터베이스 최적화 및 관리", ...]

3. **requirements_must**: 필수 요건
   - 리스트 형태로 반환
   - 예: ["Python 5년 이상 경험", "FastAPI 프레임워크 실무 경험", ...]

4. **requirements_nice**: 우대 사항
   - 리스트 형태로 반환

5. **competencies**: 요구 역량
   - 예: ["Python", "FastAPI", "PostgreSQL", "AWS"]

**중요:**
- 실제 분석 결과에 있는 내용만 사용
- 추측하거나 과장하지 말 것
- 명확하고 구체적으로 작성
"""),
        ("user", context)
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(JobPostingData)

    result = (prompt | llm).invoke({})

    # dict로 변환
    job_posting = result.model_dump()

    # List[str] → str 변환 (백엔드 API 형식에 맞게)
    job_posting["responsibilities"] = "\n".join([f"- {r}" for r in result.responsibilities])
    job_posting["requirements_must"] = "\n".join([f"- {r}" for r in result.requirements_must])
    job_posting["requirements_nice"] = "\n".join([f"- {r}" for r in result.requirements_nice])
    # competencies는 리스트 그대로 유지

    # 필수 필드들 (기본값 설정)
    job_posting["location_city"] = "서울"
    job_posting["career_level"] = "MID_SENIOR"
    job_posting["education_level"] = "Bachelor"
    job_posting["employment_type"] = "FULL_TIME"
    job_posting["status"] = "DRAFT"

    return job_posting


# 카드 데이터 스키마 정의
class JobPostingCardData(BaseModel):
    """채용공고 카드 데이터"""
    header_title: str = Field(description="카드 헤더 제목 (직무명)")
    badge_role: str = Field(description="역할 뱃지 (예: Backend, Frontend)")
    headline: str = Field(description="한 줄 요약 (매력적인 헤드라인)")
    responsibilities: List[str] = Field(description="주요 역할/업무 4개", min_length=4, max_length=4)
    requirements: List[str] = Field(description="자격 요건 4개", min_length=4, max_length=4)
    required_competencies: List[str] = Field(description="요구 역량 4개", min_length=4, max_length=4)
    company_info: str = Field(description="기업 정보 (팀 문화 + 업무 방식, 2-3문장)")
    talent_persona: str = Field(description="이상적인 인재상 (2-3문장)")
    challenge_task: str = Field(description="도전 과제 (긍정적으로 재구성, 2-3문장)")


def create_job_posting_card_from_interview(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    team_fit_analysis: TeamCultureProfile,
    job_posting_id: int,
    company_name: str,
    job_posting_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    면접 분석 결과를 LLM 기반 채용공고 카드 데이터로 변환

    Args:
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        team_fit_analysis: Situational 면접 분석 결과
        job_posting_id: 생성된 job posting ID
        company_name: 회사명
        job_posting_data: 생성된 채용공고 전체 데이터

    Returns:
        카드 POST 요청에 필요한 dict
    """
    # JD 컨텍스트 구성
    jd_context = f"""
[생성된 채용공고 (JD)]
- 제목: {job_posting_data.get('title', '')}
- 주요 업무:
{job_posting_data.get('responsibilities', '')}
- 필수 요건:
{job_posting_data.get('requirements_must', '')}
- 우대 사항:
{job_posting_data.get('requirements_nice', '')}
- 요구 역량: {', '.join(job_posting_data.get('competencies', []))}
"""

    # 컨텍스트 구성
    context = f"""
[회사 정보]
회사명: {company_name}

{jd_context}

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
- 팀 현황: {team_fit_analysis.team_situation}
- 협업 스타일: {team_fit_analysis.collaboration_style}
- 갈등 해결: {team_fit_analysis.conflict_resolution}
- 업무 환경: {team_fit_analysis.work_environment}
- 선호 스타일: {team_fit_analysis.preferred_work_style}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 채용 전문가입니다.

3단계 면접 분석 결과를 통합하여, 매력적인 채용 공고 카드를 생성하세요.

**생성 규칙:**

1. **header_title**: 직무명 (Technical 분석의 job_title 사용)

2. **badge_role**: 역할 뱃지 (예: "Backend", "Frontend", "DevOps" 등)

3. **headline**: 매력적인 한 줄 요약
   - 채용 이유와 직무를 결합하여 임팩트 있게
   - 예: "혁신적인 기술로 금융의 미래를 만들어갈 시니어 백엔드 개발자를 찾습니다"

4. **responsibilities**: 주요 역할/업무 **정확히 4개**
   - 구체적이고 명확하게

5. **requirements**: 자격 요건 **정확히 4개**

6. **required_competencies**: 요구 역량 **정확히 4개**

7. **company_info**: 기업 정보 (2-3문장)
   - General 분석의 team_culture + work_style 통합
   - 매력적으로 재구성

8. **talent_persona**: 인재상 (2-3문장)
   - General의 ideal_candidate_traits + Situational 분석 통합
   - 구체적인 특징으로 정리

9. **challenge_task**: 도전 과제 (2-3문장)
   - Technical의 expected_challenges 활용
   - 긍정적으로 재구성

**중요:**
- responsibilities, requirements, required_competencies는 **반드시 정확히 4개씩**
- 실제 분석 결과에 있는 내용만 사용
- 추측하거나 과장하지 말 것
- 일관성 있고 매력적인 공고로 작성
"""),
        ("user", context)
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.4,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(JobPostingCardData)

    result = (prompt | llm).invoke({})

    # dict로 변환 및 필수 필드 추가
    card_data = result.model_dump()
    card_data["job_posting_id"] = job_posting_id
    card_data["deadline_date"] = None  # 선택 필드

    # posting_info는 빈 dict로 (백엔드 스키마에 맞게)
    card_data["posting_info"] = {}

    return card_data
