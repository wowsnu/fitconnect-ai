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
        min_length=500,
        max_length=700
    )

    skills_text: str = Field(
        description="역량 요구사항 텍스트",
        min_length=500,
        max_length=700
    )

    growth_text: str = Field(
        description="성장 기회 제공 텍스트",
        min_length=500,
        max_length=700
    )

    career_text: str = Field(
        description="커리어 방향 텍스트",
        min_length=500,
        max_length=700
    )

    vision_text: str = Field(
        description="비전/협업 환경 텍스트",
        min_length=500,
        max_length=700
    )

    culture_text: str = Field(
        description="조직/문화 텍스트",
        min_length=500,
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
        ("system", """당신은 HR 매칭 전문가입니다.

기업의 면접 결과와 채용공고를 바탕으로, 인재와의 매칭을 위한 **6가지 기준별 텍스트**를 생성하세요.

각 텍스트는 해당 기준에서 **기업이 제공하는 가치와 요구하는 특성**을 디테일하게 드러내야 합니다.

---

## 텍스트 생성 기본 원칙 (500-700자)

**작성 원칙**:
1. **자연스러운 흐름**: 억지로 형식을 맞추지 말고, 자연스럽게 핵심 정보를 먼저 배치
2. **키워드 밀도**: 중요한 키워드(기술명, 직무명, 역량명)는 문맥을 바꿔가며 2-3회 자연스럽게 반복
3. **구체성**: 추상적 표현보다 구체적인 사례, 수치, 기술명 사용
4. **명확한 제공/요구**: 기업이 "제공하는 것"과 "요구하는 것"을 명확히 구분하여 표현

---

## 1. 역할 제공/역할 요구사항 (roles_text)

**목적**: 기업이 제공하는 역할과 요구하는 실무 경험을 명확히 합니다. (경험 기반 실무 적합성)

**기업 기준**:
- 제공하는 역할과 책임 범위
- 요구되는 경력 연차와 포지션 수준
- 담당할 주요 업무와 프로젝트
- 기대하는 성과와 결과물

**생성 가이드**:
- Technical 분석의 main_responsibilities 활용
- 구체적인 역할과 업무 범위 명시
- 요구되는 경력 수준
- 담당할 프로젝트 유형

**작성 가이드**:
- 포지션명과 주요 역할을 초반에 명확히 제시
- 핵심 업무와 기대 성과를 구체적으로 서술
- 역할 관련 키워드를 문맥을 바꿔 2-3회 반복
- 요구 경력 수준과 담당할 프로젝트 유형 명시

---

## 2. 역량 요구사항 (skills_text)

**목적**: 직무 수행에 필요한 기술 스택과 역량을 명확히 합니다. (기술·능력 기반 수행 능력)

**기업 기준**:
- 필수 기술 스택과 수준
- 필수 일반 역량 (협업, 커뮤니케이션, 문제 해결 등)
- 우대 기술 스택
- 실무에서 사용할 도구와 프레임워크

**생성 가이드**:
- Technical 분석의 required_skills, preferred_skills 활용
- competencies 리스트 포함
- 기술 스택의 우선순위
- Soft skills 요구사항

**작성 가이드**:
- 필수 기술 3-5개를 초반에 명시하고 문맥을 바꿔 반복
- 기술별 요구 숙련도를 구체적으로 표현
- Soft skills 요구사항을 업무와 연결하여 서술
- 우대 기술을 통해 추가 역량 기대 제시

---

## 3. 성장 기회 제공 (growth_text)

**목적**: 기업이 제공하는 학습 환경과 성장 기회를 명확히 합니다. (조직 중심의 장기 개발 기회)

**기업 기준**:
- 제공하는 학습 기회 (교육, 컨퍼런스, 스터디 등)
- 새로운 기술/프로젝트 도전 기회
- 멘토링 및 성장 지원 체계
- 경력 발전 경로

**생성 가이드**:
- General 분석의 work_style, team_culture 활용
- Technical의 expected_challenges를 성장 기회로 재구성
- 구체적인 성장 지원 내용

**작성 가이드**:
- 제공하는 학습 기회와 지원 체계를 구체적으로 제시
- 도전 과제와 프로젝트 기회를 성장 관점으로 표현
- 멘토링 체계와 경력 발전 경로를 명확히 서술
- 성장/학습 관련 키워드를 자연스럽게 반복

---

## 4. 커리어 방향 (career_text)

**목적**: 기업이 제공하는 커리어 경로와 방향성을 명확히 합니다. (개인 중심의 목표 적합성)

**기업 기준**:
- 제공하는 커리어 경로 (IC track, Management track)
- 성장 가능한 포지션과 역할
- 조직 내 발전 기회
- 장기적인 커리어 비전

**생성 가이드**:
- Technical의 job_title과 main_responsibilities 활용
- General의 hiring_reason과 연계
- 구체적인 승진/성장 경로

**작성 가이드**:
- 시작 포지션과 성장 경로를 명확히 제시
- IC track/Management track 등 구체적 커리어 패스 서술
- 성장 가능한 포지션과 조직 내 발전 기회 명시
- 커리어/성장 관련 키워드를 2-3회 반복

---

## 5. 비전/협업 환경 (vision_text)

**목적**: 기업의 비전과 팀 협업 환경을 명확히 합니다. (행동·기여 중심)

**기업 기준**:
- 기업/팀의 비전과 미션
- 협업 문화와 방식
- 의사결정 구조
- 팀 내 기여 방식

**생성 가이드**:
- General 분석의 core_values, team_culture 활용
- Situational 분석의 collaboration_style 활용
- 구체적인 협업 방식과 문화

**작성 가이드**:
- 기업/팀의 비전과 미션을 명확히 제시
- 협업 문화와 방식을 구체적 사례로 표현
- 의사결정 구조와 팀 내 기여 방식 서술
- 비전/협업 관련 키워드를 자연스럽게 반복

---

## 6. 조직/문화 적합도 (culture_text)

**목적**: 기업의 조직 문화와 일하는 방식을 명확히 합니다. (성향·가치관 중심)

**기업 기준**:
- 조직의 핵심 가치관
- 선호하는 업무 스타일
- 문제 해결 방식
- 커뮤니케이션 스타일

**생성 가이드**:
- General 분석의 core_values, work_style, ideal_candidate_traits 활용
- Situational 분석의 work_environment, preferred_work_style 활용
- 구체적인 문화 특성

**작성 가이드**:
- 조직의 핵심 가치관과 문화를 명확히 제시
- 선호하는 업무 스타일과 문제 해결 방식 서술
- 커뮤니케이션 스타일과 일하는 방식을 구체적으로 표현
- 문화/가치관 관련 키워드를 2-3회 반복

---

**중요 사항**:
- 각 텍스트는 **500-700자**로 작성
- 면접에서 드러난 **실제 내용**만 사용, 추측 금지
- 생성된 채용공고 데이터와 일관성 유지
- 각 기준별 작성 가이드를 따라 키워드 밀도와 자연스러운 흐름 유지
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
