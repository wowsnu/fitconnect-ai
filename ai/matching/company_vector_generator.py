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
        min_length=50
    )

    skills_text: str = Field(
        description="역량 요구사항 텍스트",
        min_length=50
    )

    growth_text: str = Field(
        description="성장 기회 제공 텍스트",
        min_length=50
    )

    career_text: str = Field(
        description="커리어 방향 텍스트",
        min_length=50
    )

    vision_text: str = Field(
        description="비전/협업 환경 텍스트",
        min_length=50
    )

    culture_text: str = Field(
        description="조직/문화 텍스트",
        min_length=50
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

각 텍스트는 해당 기준에서 **기업이 제공하는 가치와 요구하는 특성**을 명확히 드러내야 합니다.

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

**예시 형식**:
"시니어 백엔드 개발자로서 AI 추천 시스템 API 설계 및 개발을 주도. Redis 기반 캐싱 전략 수립과 성능 최적화 담당. 실시간 처리 시스템 아키텍처 설계 및 구현. 주니어 개발자 멘토링과 코드 리뷰 리드. 월 1억 이상 트래픽 처리하는 확장 가능한 백엔드 시스템 구축 기대."

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

**예시 형식**:
"필수 기술: Python/FastAPI 실무 5년 이상, PostgreSQL 쿼리 최적화 경험, Redis 캐싱 전략 수립 경험, AWS 인프라 운영 경험. 필수 역량: 협업 능력(높음), 문제 해결 능력(높음), 커뮤니케이션(높음). 우대 기술: Kubernetes, Kafka, Elasticsearch, MSA 아키텍처 설계 경험."

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

**예시 형식**:
"분산 시스템과 MSA 전환 프로젝트 참여 기회. 대규모 트래픽 처리 경험 축적 가능. 시니어 엔지니어의 1:1 멘토링 제공. 컨퍼런스 참가 및 기술 블로그 작성 지원. 새로운 기술 스택 도입 시 주도적 역할 부여. 테크 리드/아키텍트로 성장 경로 제공."

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

**예시 형식**:
"시니어 백엔드 개발자에서 시작하여 테크 리드로 성장 가능. IC track으로 Staff Engineer, Principal Engineer까지 커리어 패스 제공. 대규모 시스템 아키텍처 설계 경험 축적. 신규 서비스 런칭 시 테크 리딩 기회. 조직 확장에 따른 팀 리드 포지션 기회."

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

**예시 형식**:
"AI 기술로 금융의 미래를 만드는 비전 추구. 데이터 기반 의사결정과 논리적 토론 문화. 코드 리뷰와 페어 프로그래밍 일상화. 2주 스프린트 애자일 개발. 팀원 모두가 의사결정에 참여하는 수평적 문화. 기술 블로그와 사내 세미나를 통한 지식 공유 활성화."

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

**예시 형식**:
"핵심 가치: 혁신, 도전, 투명성, 협력. 자율적이고 책임감 있는 업무 문화. 실패를 학습의 기회로 보는 도전적 환경. 데이터와 논리 기반의 분석적 문제 해결 선호. 직급보다 전문성을 존중하는 수평적 소통. 빠른 의사결정과 실행력 중시. 애자일하고 유연한 조직 문화."

---

**중요 사항**:
- 각 텍스트는 **50자 이상, 400자 이하**로 작성
- 면접에서 드러난 **실제 내용**만 사용, 추측 금지
- 생성된 채용공고 데이터와 일관성 유지
- 구체적인 수치, 사례, 키워드 포함
- 간결하고 명확하게 작성
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
