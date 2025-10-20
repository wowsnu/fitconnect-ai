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
    responsibilities: List[str] = Field(description="주요 업무 (자유 개수, 구체적으로)")
    requirements_must: List[str] = Field(description="필수 요건 (자유 개수, 구체적으로)")
    requirements_nice: List[str] = Field(description="우대 요건 (자유 개수)")
    competencies: List[str] = Field(description="요구 역량 (자유 개수)")


def create_job_posting_from_interview(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    team_fit_analysis: TeamCultureProfile,
    company_profile: Optional[Dict[str, Any]] = None,
    existing_jd: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    면접 분석 결과를 LLM 기반 채용공고 데이터로 변환

    Args:
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        team_fit_analysis: Situational 면접 분석 결과
        company_profile: 기업 프로필 정보 (선택)
        existing_jd: 기존 채용공고 데이터 (선택)

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

1. **title**: 직무명 (한글로 작성)

2. **responsibilities**: 주요 업무 (한글로)
   - 리스트 형태로 반환
   - **중요: 3개~7개 사이로 작성**
   - 분석 결과에 따라 필요한 만큼 유연하게 작성
   - 구체적이고 명확하게 작성
   - 예: ["RESTful API 설계 및 개발", "데이터베이스 최적화 및 관리", "CI/CD 파이프라인 구축", "모니터링 시스템 운영", "기술 문서 작성"]

3. **requirements_must**: 필수 요건 (한글로)
   - 리스트 형태로 반환
   - **중요: 3개~7개 사이로 작성**
   - 분석 결과에 따라 필요한 만큼 유연하게 작성
   - 예: ["컴퓨터공학 전공", "Python 5년 이상 경험", "클라우드 인프라 구축 경험", "대규모 트래픽 처리 경험", "팀 리딩 경험"]

4. **requirements_nice**: 우대 사항 (한글로)
   - 리스트 형태로 반환
   - **중요: 3개~7개 사이로 작성**
   - 분석 결과에 따라 필요한 만큼 유연하게 작성

5. **competencies**: 요구 역량 (한글로)
   - 리스트 형태로 반환
   - **중요: 3개~7개 사이로 작성**
   - 분석 결과에서 언급된 모든 기술/역량을 포함하여 구체적인 수준까지 기술
   - 예: ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "Kubernetes", "Redis", "Kafka"]

**중요:**
- 모든 내용을 한글로만 작성 (기술 용어도 한글 표기 우선)
- **4개로 고정하지 마세요** - 분석 결과에 따라 3~7개(competencies는 5~10개) 사이로 유연하게
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
    job_posting["competencies"] = ", ".join(result.competencies)  # List → 문자열 변환

    # 4개 필드만 반환 (기존 JD에 덮어쓰기 용)
    return {
        "responsibilities": job_posting["responsibilities"],
        "requirements_must": job_posting["requirements_must"],
        "requirements_nice": job_posting["requirements_nice"],
        "competencies": job_posting["competencies"]
    }


# 카드 데이터 스키마 정의
class JobPostingCardData(BaseModel):
    """채용공고 카드 데이터"""
    header_title: str = Field(description="카드 헤더 제목 (직무명, 한글)")
    badge_role: str = Field(description="역할 뱃지 (예: 백엔드, 프론트엔드)")
    headline: str = Field(description="한 줄 요약 (매력적인 헤드라인, 한글)")
    responsibilities: List[str] = Field(description="주요 역할/업무 4개 (한글)", min_length=4, max_length=4)
    requirements: List[str] = Field(description="자격 요건 4개 (한글)", min_length=4, max_length=4)
    required_competencies: List[str] = Field(description="요구 역량 4개 (구체적으로: 기술명 + 경력/수준, 한글)", min_length=4, max_length=4)
    company_info: str = Field(description="기업 정보 (팀 문화 + 업무 방식, 1문장으로 요약, 한글)")
    talent_persona: str = Field(description="이상적인 인재상 (1문장, 한글)")
    challenge_task: str = Field(description="도전 과제 (긍정적으로 재구성, 1문장으로 요약 , 한글)")


def create_job_posting_card_from_interview(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    team_fit_analysis: TeamCultureProfile,
    job_posting_id: int,
    company_name: str,
    job_posting_data: Dict[str, Any],
    company_profile: Optional[Dict[str, Any]] = None
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
- 요구 역량: {job_posting_data.get('competencies', '')}
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

1. **header_title**: 직무명 (한글로 작성)

2. **badge_role**: 역할 뱃지 (한글로: "백엔드", "프론트엔드", "데브옵스" 등)

3. **headline**: 매력적인 한 줄 요약 (한글로)
   - 채용 이유와 직무를 결합하여 임팩트 있게
   - 예: "혁신적인 기술로 금융의 미래를 만들어갈 시니어 백엔드 개발자를 찾습니다"

4. **responsibilities**: 주요 역할/업무 **정확히 4개** (한글로)
   - 구체적이고 명확하게
   - 예: "RESTful API 설계 및 개발", "마이크로서비스 아키텍처 설계"

5. **requirements**: 자격 요건 **정확히 4개** (한글로)
   - 예: "컴퓨터공학 또는 관련 학과 전공", "5년 이상의 백엔드 개발 경력"

6. **required_competencies**: 요구 역량 **정확히 4개** (구체적으로, 한글로)
   - **중요**: 기술/언어명 + 경력 또는 숙련도 필수 포함
   - ✅ 좋은 예: "Python 5년 이상 실무 경험", "React 고급 수준", "AWS 클라우드 3년 이상", "Docker/Kubernetes 중급 이상"
   - ❌ 나쁜 예: "Python", "React", "AWS", "Docker" (이렇게 기술명만 나열하지 마세요)
   - 면접 분석에서 파악된 필요 경력 수준을 반영할 것

7. **company_info**: 기업 정보 (1문장으로 요약, 한글로)
   - General 분석의 team_culture + work_style 통합
   - 매력적으로 재구성

8. **talent_persona**: 인재상 (1문장으로 요약, 한글로)
   - General의 ideal_candidate_traits + Situational 분석 통합
   - 구체적인 특징으로 정리

9. **challenge_task**: 도전 과제 (1문장으로 요약, 한글로)
   - Technical의 expected_challenges 활용
   - 긍정적으로 재구성

**중요:**
- 모든 내용을 한글로만 작성 (기술명도 한글로, 또는 영문 기술명에 한글 설명 추가)
- responsibilities, requirements, required_competencies는 **반드시 정확히 4개씩**
- required_competencies는 반드시 경력/수준을 포함하여 구체적으로 작성
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
    card_data["deadline_date"] = job_posting_data.get("deadline_date")

    # posting_info에 회사 기본 정보 추가
    posting_info = {}
    if company_profile:
        basic = company_profile.get("basic", {})
        about = company_profile.get("about", {})

        posting_info = {
            "company_name": basic.get("name", company_name),
            "company_description": about.get("description", ""),
            "company_culture": about.get("culture", ""),
            "vision_mission": about.get("vision_mission", ""),
            "business_domains": about.get("business_domains", ""),
            "website_url": basic.get("website_url", ""),
            "logo_url": basic.get("logo_url", ""),
        }
        print(f"[INFO] Added company profile to card posting_info")

    card_data["posting_info"] = posting_info

    return card_data
