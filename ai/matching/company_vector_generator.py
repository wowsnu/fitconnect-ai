"""
Company Matching Vector Generator (기업용)

기업 면접 결과를 바탕으로 6가지 매칭 기준별 텍스트 생성:
1. 역할 적합도/역할 제공 (vector_roles)
2. 역량 적합도 (vector_skills)
3. 성장 기회 제공 (vector_growth)
4. 커리어 방향 (vector_career)
5. 비전 신뢰도/협업 환경 (vector_vision)
6. 조직/문화 적합도 (vector_culture)

인재용 vector_generator.py와 동일한 구조로 구현
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.company.models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    TeamCultureProfile
)
from config.settings import get_settings


class CompanyMatchingTexts(BaseModel):
    """기업 매칭용 6가지 텍스트"""

    roles_text: str = Field(
        description="역할 제공/역할 요구사항 텍스트",
        max_length=700
    )

    skills_text: str = Field(
        description="역량 요구사항 텍스트",
        max_length=700
    )

    growth_text: str = Field(
        description="성장 기회 제공 텍스트",
        max_length=700
    )

    career_text: str = Field(
        description="커리어 방향 텍스트",
        max_length=700
    )

    vision_text: str = Field(
        description="비전/협업 환경 텍스트",
        max_length=700
    )

    culture_text: str = Field(
        description="조직/문화 텍스트",
        max_length=700
    )


def generate_company_matching_texts(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    team_fit_analysis: TeamCultureProfile,
    company_name: str,
    job_posting_data: Dict[str, Any]
) -> CompanyMatchingTexts:
    """
    기업 면접 결과를 바탕으로 6가지 매칭 텍스트 생성

    Args:
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        team_fit_analysis: Situational 면접 분석 결과
        company_name: 회사명
        job_posting_data: 생성된 채용공고 데이터

    Returns:
        CompanyMatchingTexts (6가지 매칭 텍스트)
    """

    # 채용공고 요약
    jd_summary = f"""
[생성된 채용공고]
- 직무명: {job_posting_data.get('title', '')}
- 주요 업무:
{job_posting_data.get('responsibilities', '')}
- 필수 요건:
{job_posting_data.get('requirements_must', '')}
- 우대 요건:
{job_posting_data.get('requirements_nice', '')}
- 필요 역량: {', '.join(job_posting_data.get('competencies', []))}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 매칭 전문가입니다.

기업의 면접 결과와 채용공고를 바탕으로, 인재와의 매칭을 위한 **6가지 텍스트**를 생성하세요.

---

## 핵심 작성 원칙

### 1. 쉬운 말로 쓰기
- 전문용어나 어려운 단어 대신 **일상적인 표현** 사용
- 예시:
  - ❌ "크로스펑셔널 협업 환경" → ✅ "여러 팀과 함께 일하는 환경"
  - ❌ "애자일 방법론 기반" → ✅ "빠르게 시도하고 개선하는 방식"
  - ❌ "자율적 의사결정 권한" → ✅ "스스로 결정하고 진행할 수 있는 환경"

### 2. 도구보다 '뭘 할 수 있는지' 강조
- 도구 이름만 나열하지 말고, **그걸로 뭘 하는지** 설명
- 예시:
  - ❌ "React 필수" → ✅ "화면 개발 경험 필요 (React 사용)"
  - ❌ "Kubernetes 운영" → ✅ "서버 관리 및 배포 경험 (Kubernetes 환경)"

### 3. 경험 수준을 명확하게
- 원하는 경력 수준을 솔직하게 표현
- **신입/주니어 원함**: "배우려는 자세", "함께 성장", "기초부터"
- **경력자 원함**: "혼자서 담당 가능", "경험 있는 분", "직접 해본 분"
- **시니어 원함**: "팀을 이끌 수 있는", "전체를 설계할 수 있는"

### 4. 회사 성향은 구체적으로
- 모호한 표현 대신 **실제로 어떻게 일하는지** 설명
- 예시:
  - ❌ "자유로운 문화" → ✅ "출퇴근 시간이 자유롭고, 재택근무도 가능"
  - ❌ "수평적 조직" → ✅ "직급 상관없이 의견 내고, 회의에서 자유롭게 토론"
  - ❌ "성장 지원" → ✅ "컨퍼런스 참가비 지원, 매달 책값 지원"

---

## 텍스트별 작성 가이드 (각 500-700자)

### 1. 역할/업무 (roles_text)
**이 포지션에서 어떤 일을 하는지**
- 맡게 될 주요 업무
- 어느 정도 경력이 필요한지
- 어떤 프로젝트를 담당하는지
- 기대하는 결과물

### 2. 필요 역량 (skills_text)
**어떤 능력이 필요한지**
- 필수로 필요한 기술 (도구 이름 + 그걸로 뭘 하는지)
- 있으면 좋은 기술
- 기술 외에 필요한 능력 (소통, 협업 등)

### 3. 성장 기회 (growth_text)
**여기서 뭘 배우고 성장할 수 있는지**
- 회사에서 제공하는 학습 기회
- 도전해볼 수 있는 새로운 프로젝트
- 선배/멘토에게 배울 수 있는 환경인지

### 4. 커리어 방향 (career_text)
**앞으로 어떻게 성장할 수 있는지**
- 시작 포지션과 그 다음 단계
- 전문가 트랙 vs 관리자 트랙 가능 여부
- 장기적으로 어떤 역할이 될 수 있는지

### 5. 협업 방식 (vision_text)
**팀에서 어떻게 함께 일하는지**
- 팀원들과 어떻게 소통하는지
- 의견 충돌 시 어떻게 해결하는지
- 회의나 협업 방식

### 6. 회사 문화 (culture_text)
**어떤 분위기에서 일하는지**
- 일하는 스타일 (빠르게 vs 꼼꼼하게, 혼자 vs 같이)
- 어떤 성격의 사람이 잘 맞는지
- 출퇴근, 재택, 복지 등 환경

---

**중요**:
- 각 텍스트 **500-700자**
- 면접에서 나온 **실제 이야기**만 사용 (추측 금지)
- **전문용어 쓰지 않기** - 일반인이 읽어도 이해되게
- 원하는 경험 수준을 솔직하게 (경험 많이 원하면 많다고, 적어도 되면 적어도 된다고)
"""),
        ("user", f"""
## 회사 정보
- 회사명: {company_name}

{jd_summary}

## General 면접 분석 - 회사 문화 & 가치
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}
- 업무 방식: {general_analysis.work_style}
- 채용 이유: {general_analysis.hiring_reason}
- 채용 이유 심층 분석: {general_analysis.hiring_reason_reasoning}

## Technical 면접 분석 - 직무 정보
- 직무명: {technical_requirements.job_title}
- 주요 업무: {', '.join(technical_requirements.main_responsibilities)}
- 필수 역량: {', '.join(technical_requirements.required_skills)}
- 우대 역량: {', '.join(technical_requirements.preferred_skills)}
- 예상 도전 과제: {technical_requirements.expected_challenges}
- 예상 도전 과제 심층 분석: {technical_requirements.expected_challenges_reasoning}

## Situational 면접 분석 - 팀 문화 & 협업
- 팀 현황: {team_fit_analysis.team_situation}
- 팀 현황 심층 분석: {team_fit_analysis.team_situation_reasoning}
- 협업 스타일: {team_fit_analysis.collaboration_style}
- 협업 스타일 심층 분석: {team_fit_analysis.collaboration_style_reasoning}
- 갈등 해결: {team_fit_analysis.conflict_resolution}
- 갈등 해결 심층 분석: {team_fit_analysis.conflict_resolution_reasoning}
- 업무 환경: {team_fit_analysis.work_environment}
- 업무 환경 심층 분석: {team_fit_analysis.work_environment_reasoning}
- 선호 업무 스타일: {team_fit_analysis.preferred_work_style}
- 선호 업무 스타일 심층 분석: {team_fit_analysis.preferred_work_style_reasoning}

---

위 정보를 바탕으로 6가지 매칭 텍스트를 생성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(CompanyMatchingTexts)

    return (prompt | llm).invoke({})


def generate_company_matching_vectors(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    team_fit_analysis: TeamCultureProfile,
    company_name: str,
    job_posting_data: Dict[str, Any]
) -> dict:
    """
    기업 면접 결과로부터 6가지 매칭 벡터 생성 (텍스트 생성 + 임베딩)

    Args:
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        team_fit_analysis: Situational 면접 분석 결과
        company_name: 회사명
        job_posting_data: 생성된 채용공고 데이터

    Returns:
        {
            "texts": {
                "roles_text": str,
                "skills_text": str,
                ...
            },
            "vectors": {
                "vector_roles": {"embedding": [float, ...]},
                "vector_skills": {"embedding": [float, ...]},
                ...
            },
            "role": "company"
        }
    """
    from ai.matching.embedding import embed_matching_texts

    # 1. 6가지 매칭 텍스트 생성 (LLM)
    texts = generate_company_matching_texts(
        general_analysis=general_analysis,
        technical_requirements=technical_requirements,
        team_fit_analysis=team_fit_analysis,
        company_name=company_name,
        job_posting_data=job_posting_data
    )

    # 2. 텍스트를 벡터로 임베딩
    vectors = embed_matching_texts(
        roles_text=texts.roles_text,
        skills_text=texts.skills_text,
        growth_text=texts.growth_text,
        career_text=texts.career_text,
        vision_text=texts.vision_text,
        culture_text=texts.culture_text
    )

    return {
        "texts": {
            "roles_text": texts.roles_text,
            "skills_text": texts.skills_text,
            "growth_text": texts.growth_text,
            "career_text": texts.career_text,
            "vision_text": texts.vision_text,
            "culture_text": texts.culture_text
        },
        "vectors": vectors,
        "role": "company"
    }
