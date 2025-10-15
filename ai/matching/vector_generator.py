"""
Matching Vector Generator (인재용)

3가지 면접 결과를 바탕으로 6가지 매칭 기준별 텍스트 생성:
1. 역할 적합도/역할 수행력 (vector_roles)
2. 역량 적합도 (vector_skills)
3. 성장 기회 제공/성장 가능성 (vector_growth)
4. 커리어 방향 (vector_career)
5. 비전 신뢰도/협업 기여도 (vector_vision)
6. 조직/문화 적합도 (vector_culture)
"""

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ai.interview.talent.models import (
    CandidateProfile,
    GeneralInterviewAnalysis,
    FinalPersonaReport
)
from config.settings import get_settings


class TalentMatchingTexts(BaseModel):
    """인재 매칭용 6가지 텍스트"""

    roles_text: str = Field(
        description="역할 적합도/역할 수행력 텍스트",
        min_length=50
    )

    skills_text: str = Field(
        description="역량 적합도 텍스트",
        min_length=50
    )

    growth_text: str = Field(
        description="성장 기회 제공/성장 가능성 텍스트",
        min_length=50
    )

    career_text: str = Field(
        description="커리어 방향 텍스트",
        min_length=50
    )

    vision_text: str = Field(
        description="비전 신뢰도/협업 기여도 텍스트",
        min_length=50
    )

    culture_text: str = Field(
        description="조직/문화 적합도 텍스트",
        min_length=50
    )


def generate_talent_matching_texts(
    candidate_profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    technical_results: dict,
    situational_report: FinalPersonaReport
) -> TalentMatchingTexts:
    """
    인재의 면접 결과를 바탕으로 6가지 매칭 텍스트 생성

    Args:
        candidate_profile: 지원자 기본 프로필
        general_analysis: 구조화 면접 분석
        technical_results: 직무 적합성 면접 결과
        situational_report: 상황 면접 페르소나 리포트

    Returns:
        TalentMatchingTexts (6가지 매칭 텍스트)
    """

    # 경력 정보 요약
    experience_summary = "\n".join([
        f"- {exp.company_name} / {exp.title} ({exp.duration_years or 0}년)"
        for exp in candidate_profile.experiences
    ]) if candidate_profile.experiences else "경력 없음"

    # 기술 면접 결과에서 질문/답변 추출
    skills_evaluated = technical_results.get("skills_evaluated", [])
    results = technical_results.get("results", {})

    technical_qa_summary = ""
    for skill in skills_evaluated:
        skill_qa = results.get(skill, [])
        if skill_qa:
            technical_qa_summary += f"\n### {skill}\n"
            for qa in skill_qa:
                technical_qa_summary += f"Q: {qa.get('question', '')}\n"
                technical_qa_summary += f"A: {qa.get('answer', '')[:200]}...\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 매칭 전문가입니다.

인재의 면접 결과를 바탕으로, 기업과의 매칭을 위한 **6가지 기준별 텍스트**를 생성하세요.

각 텍스트는 해당 기준에서 **인재가 제공할 수 있는 가치와 특성**을 명확히 드러내야 합니다.

---

## 1. 역할 적합도/역할 수행력 (roles_text)

**목적**: 후보자가 해당 직무에서 요구되는 핵심 역할과 업무를 효과적으로 수행할 수 있는지를 평가합니다. (경험 기반 실무 적합성)

**인재 기준**:
- 주요 경험/경력 (경력 연차·포지션)
- 직무 수행 (업무 수행 사례)

**생성 가이드**:
- 구체적인 경력 연차와 포지션
- 실제 수행한 프로젝트와 업무 사례
- 담당했던 역할과 책임 범위
- 성과와 결과물

**예시 형식**:
"백엔드 개발자로 3년 경력. AI 추천 시스템 API 개발을 주도하여 Redis 캐싱으로 응답 속도 70% 개선. 실시간 채팅 서버 개발에서 WebSocket과 Redis Pub/Sub를 활용해 동시 접속자 5만명 처리 시스템 구축. 성능 최적화와 확장 가능한 아키텍처 설계 경험 보유."

---

## 2. 역량 적합도 (skills_text)

**목적**: 후보자가 직무 수행에 필요한 일반 역량과 직무 관련 역량 및 기술을 얼마나 갖추었는지를 평가합니다. (기술·능력 기반 수행 능력)

**인재 기준**:
- 강점
- 핵심 일반 역량
- 핵심 직무 역량/기술 (Skill Set)

**생성 가이드**:
- 기술 스택과 수준 (높음/보통/낮음)
- Soft skills (협업, 커뮤니케이션, 리더십 등)
- 강점으로 드러난 능력
- 실무에서 검증된 역량

**예시 형식**:
"강점: 성능 최적화 및 확장 가능한 아키텍처 설계 능력, 비동기 처리 및 캐싱 전략. 핵심 일반 역량: 협업 능력(높음), 문제 해결 능력(높음), 커뮤니케이션(높음). 핵심 기술: FastAPI 비동기 처리(높음), PostgreSQL 인덱싱 및 쿼리 최적화(높음), Redis 캐싱(높음)."

---

## 3. 성장 기회 제공/성장 가능성 (growth_text)

**목적**: 후보자가 조직에서 장기적으로 성장하고 발전할 잠재력이 있는지를 평가합니다. (조직 중심의 장기 개발 가능성)

**인재 기준**:
- 강점
- 성장 가능성 (학습 의지, 새로운 역할·기술 수용 능력)
- 직무 수행 (경력 확장 가능성)

**생성 가이드**:
- 학습 성향과 방식
- 새로운 기술/분야에 대한 수용력
- 자기 개발 노력 (블로그, 오픈소스 등)
- 경력 확장 가능성

**예시 형식**:
"실습 중심 학습으로 빠른 기술 습득력 보유. 기술 블로그 운영 및 오픈소스 기여를 통한 지속적 성장. 분산 시스템과 MSA 아키텍처에 대한 학습 의지. 성능 최적화 전문성을 기반으로 대규모 시스템 설계로 경력 확장 가능."

---

## 4. 커리어 방향 (career_text)

**목적**: 후보자의 경력 목표와 조직의 성장 방향 및 직무 기회가 얼마나 일치하는지를 평가합니다. (개인 중심의 목표 적합성)

**인재 기준**:
- 주요 경험/경력 (향후 성장 계획)
- 성장 가능성 (커리어 방향)

**생성 가이드**:
- 현재 경력 경로
- 향후 목표 직무/포지션
- 관심 분야와 기술
- 장기 커리어 비전

**예시 형식**:
"현재 백엔드 개발 3년차로 성능 최적화와 아키텍처 설계 경험 축적. 목표는 시니어 백엔드 엔지니어로 성장하여 대규모 트래픽 처리 시스템 설계. 분산 시스템, MSA 아키텍처, 대용량 데이터 처리 분야에 깊은 관심."

---

## 5. 비전 신뢰도/협업 기여도 (vision_text)

**목적**: 후보자가 조직의 비전과 전략을 이해·공감하며, 팀 내 협업과 기여에 긍정적인 영향을 줄 수 있는지를 평가합니다. (행동·기여 중심)

**인재 기준**:
- 협업 성향 (팀 내 기여 방식)
- 핵심 일반 역량

**생성 가이드**:
- 협업 스타일과 커뮤니케이션 방식
- 팀 내 기여 방식
- 의사결정 참여 방식
- 갈등 해결 접근법

**예시 형식**:
"논리적 소통과 데이터 기반 의사결정으로 팀 내 의견 조율에 능숙. 코드 리뷰와 페어 프로그래밍을 선호하며 적극적으로 지식 공유. 의견 충돌 시 근거를 기반으로 합리적 합의 도출. 팀원들과 함께 성장하는 것을 중요하게 생각."

---

## 6. 조직/문화 적합도 (culture_text)

**목적**: 후보자의 가치관과 성향이 조직 문화와 얼마나 잘 맞는지를 평가합니다. (성향·가치관 중심)

**인재 기준**:
- 협업 성향 (커뮤니케이션 방식)
- 핵심 일반 역량 (조직 문화 적응력)

**생성 가이드**:
- 업무 스타일 (주도형, 협력형, 독립형)
- 문제 해결 방식 (분석형, 직관형, 실행형)
- 스트레스 대응 방식 (도전형, 안정형)
- 커뮤니케이션 스타일 (논리형, 공감형, 간결형)

**예시 형식**:
"협력적이고 체계적인 업무 스타일. 데이터 기반의 분석적 문제 해결 선호. 도전적인 환경에서 학습과 성장을 추구. 논리적이면서도 공감적인 커뮤니케이션. 애자일 환경과 기술 토론이 활발한 팀 문화에 적합."

---

**중요 사항**:
- 각 텍스트는 **50자 이상, 300자 이하**로 작성
- 면접에서 드러난 **실제 내용**만 사용, 추측 금지
- 구체적인 수치, 사례, 키워드 포함
- 간결하고 명확하게 작성
"""),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 총 경력: {sum((exp.duration_years or 0) for exp in candidate_profile.experiences)}년

## 경력 사항
{experience_summary}

## 구조화 면접 분석
- 주요 테마: {", ".join(general_analysis.key_themes)}
- 관심 분야: {", ".join(general_analysis.interests)}
- 강조한 경험: {", ".join(general_analysis.emphasized_experiences)}
- 업무 스타일: {", ".join(general_analysis.work_style_hints)}
- 기술 키워드: {", ".join(general_analysis.technical_keywords)}

## 직무 적합성 면접 결과
{technical_qa_summary}

## 상황 면접 페르소나
- 업무 스타일: {situational_report.work_style}
  (근거: {situational_report.work_style_reason})
- 문제 해결: {situational_report.problem_solving}
  (근거: {situational_report.problem_solving_reason})
- 학습 성향: {situational_report.learning}
  (근거: {situational_report.learning_reason})
- 스트레스 대응: {situational_report.stress_response}
  (근거: {situational_report.stress_response_reason})
- 커뮤니케이션: {situational_report.communication}
  (근거: {situational_report.communication_reason})
- 요약: {situational_report.summary}
- 추천 팀 환경: {situational_report.team_fit}

---

위 정보를 바탕으로 6가지 매칭 텍스트를 생성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TalentMatchingTexts)

    return (prompt | llm).invoke({})



def generate_talent_matching_vectors(
    candidate_profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    technical_results: dict,
    situational_report: FinalPersonaReport
) -> dict:
    """
    인재의 면접 결과로부터 6가지 매칭 벡터 생성 (텍스트 생성 + 임베딩)

    Args:
        candidate_profile: 지원자 기본 프로필
        general_analysis: 구조화 면접 분석
        technical_results: 직무 적합성 면접 결과
        situational_report: 상황 면접 페르소나 리포트

    Returns:
        {
            "texts": {
                "roles_text": str,
                "skills_text": str,
                ...
            },
            "vectors": {
                "vector_roles": [float, ...],
                "vector_skills": [float, ...],
                ...
            },
            "role": "talent"
        }
    """
    from ai.matching.embedding import embed_matching_texts

    # 1. 6가지 매칭 텍스트 생성 (LLM)
    texts = generate_talent_matching_texts(
        candidate_profile=candidate_profile,
        general_analysis=general_analysis,
        technical_results=technical_results,
        situational_report=situational_report
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
        "vectors": vectors
    }

