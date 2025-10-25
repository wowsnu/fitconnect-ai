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
    TechnicalInterviewAnalysis,
    FinalPersonaReport
)
from config.settings import get_settings


class TalentMatchingTexts(BaseModel):
    """인재 매칭용 6가지 텍스트"""

    roles_text: str = Field(
        description="역할 적합도/역할 수행력 텍스트",
        min_length=500,
        max_length=700
    )

    skills_text: str = Field(
        description="역량 적합도 텍스트",
        min_length=500,
        max_length=700
    )

    growth_text: str = Field(
        description="성장 기회 제공/성장 가능성 텍스트",
        min_length=500,
        max_length=700
    )

    career_text: str = Field(
        description="커리어 방향 텍스트",
        min_length=500,
        max_length=700
    )

    vision_text: str = Field(
        description="비전 신뢰도/협업 기여도 텍스트",
        min_length=500,
        max_length=700
    )

    culture_text: str = Field(
        description="조직/문화 적합도 텍스트",
        min_length=500,
        max_length=700
    )


def generate_talent_matching_texts(
    candidate_profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    technical_analysis: TechnicalInterviewAnalysis,
    situational_report: FinalPersonaReport
) -> TalentMatchingTexts:
    """
    인재의 면접 결과를 바탕으로 6가지 매칭 텍스트 생성

    Args:
        candidate_profile: 지원자 기본 프로필
        general_analysis: 구조화 면접 분석
        technical_analysis: 직무 적합성 면접 분석
        situational_report: 상황 면접 페르소나 리포트

    Returns:
        TalentMatchingTexts (6가지 매칭 텍스트)
    """

    # 경력 정보 요약
    experience_summary = "\n".join([
        f"- {exp.company_name} / {exp.title} ({exp.duration_years or 0}년)" +
        (f"\n  요약: {exp.summary}" if exp.summary else "")
        for exp in candidate_profile.experiences
    ]) if candidate_profile.experiences else "경력 없음"

    # 학력 정보 요약
    education_summary = "\n".join([
        f"- {edu.school_name}" +
        (f" / {edu.major}" if edu.major else "") +
        f" ({edu.status})"
        for edu in candidate_profile.educations
    ]) if candidate_profile.educations else "학력 정보 없음"

    # 활동 정보 요약
    activity_summary = "\n".join([
        f"- {act.name}" +
        (f" ({act.category})" if act.category else "") +
        (f": {act.description}" if act.description else "")
        for act in candidate_profile.activities
    ]) if candidate_profile.activities else "활동 정보 없음"

    # 자격증 정보 요약
    certification_summary = "\n".join([
        f"- {cert.name}" +
        (f" ({cert.score_or_grade})" if cert.score_or_grade else "")
        for cert in candidate_profile.certifications
    ]) if candidate_profile.certifications else "자격증 없음"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 HR 매칭 전문가입니다.

인재의 면접 결과를 바탕으로, 기업과의 매칭을 위한 **6가지 기준별 텍스트**를 생성하세요.

각 텍스트는 해당 기준에서 **인재가 제공할 수 있는 가치와 특성**을 디테일하게 드러내야 합니다.

---

## 텍스트 생성 기본 원칙 (500-700자)

**작성 원칙**:
1. **자연스러운 흐름**: 억지로 형식을 맞추지 말고, 자연스럽게 핵심 정보를 먼저 배치
2. **키워드 밀도**: 중요한 키워드(기술명, 직무명, 역량명)는 문맥을 바꿔가며 2-3회 자연스럽게 반복
3. **구체성**: 추상적 표현보다 구체적인 사례, 수치, 기술명 사용
4. **희망 조건 반영**: 아래 희망 조건을 각 기준에 맞게 자연스럽게 녹여낼 것

**희망 조건 활용 가이드**:
- **역할/역량**: 희망 직무를 고려한 역할 및 기술 강조
- **성장/커리어**: 희망 직무/산업 방향성을 성장 목표로 연결
- **문화**: 희망 회사규모/근무지를 선호 업무 환경으로 표현

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

**작성 가이드**:
- 직무명, 연차, 핵심 전문 분야를 초반에 명확히 제시
- 최근 주요 프로젝트 2-3개를 정량적 성과와 함께 서술
- 핵심 역할 키워드를 문맥을 바꿔 2-3회 자연스럽게 반복
- 희망 직무와 현재 경험의 연결점 강조

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

**작성 가이드**:
- 핵심 기술 스택 3-5개를 초반에 명시하고 문맥을 바꿔 반복
- 기술 숙련도와 실무 검증 사례를 구체적으로 서술
- Soft skills를 프로젝트 경험과 연결하여 표현
- 희망 직무 관련 기술을 강조

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

**작성 가이드**:
- 학습 성향과 방식을 구체적 사례와 함께 제시
- 자기개발 활동(블로그, 오픈소스 등)을 명시
- 희망 산업/직무와 연결된 성장 방향 강조
- 기술 습득 경험을 통해 성장 잠재력 입증

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

**작성 가이드**:
- 현재 경력과 목표 방향을 명확히 제시
- 희망 직무/산업을 커리어 목표로 자연스럽게 연결
- 관심 기술 분야와 장기 비전을 구체적으로 서술
- 목표 키워드(직무명, 산업명)를 2-3회 반복

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

**작성 가이드**:
- 협업 스타일과 커뮤니케이션 방식을 구체적 사례로 표현
- 팀 내 기여 방식과 의사결정 참여 경험 서술
- 갈등 해결 경험을 통해 협업 역량 입증
- 협업/기여 관련 키워드를 자연스럽게 반복

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

**작성 가이드**:
- 업무 스타일과 선호 환경을 페르소나 분석 결과와 함께 제시
- 희망 회사규모/근무지를 선호 업무 환경으로 자연스럽게 표현
- 문제 해결 방식, 스트레스 대응, 커뮤니케이션 스타일을 구체적으로 서술
- 성향/가치관 관련 키워드를 반복

---

**중요 사항**:
- 각 텍스트는 **500-700자**로 작성
- 면접에서 드러난 **실제 내용**만 사용, 추측 금지
- 각 기준별 작성 구조를 따라 핵심 정보를 앞쪽에 집중 배치
"""),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 한줄소개: {candidate_profile.basic.tagline if candidate_profile.basic and candidate_profile.basic.tagline else "없음"}
- 총 경력: {sum((exp.duration_years or 0) for exp in candidate_profile.experiences)}년

## 희망 조건
- 희망 직무: {candidate_profile.basic.desired_role if candidate_profile.basic and candidate_profile.basic.desired_role else "정보 없음"}
- 희망 연봉: {candidate_profile.basic.desired_salary if candidate_profile.basic and candidate_profile.basic.desired_salary else "정보 없음"}
- 희망 산업: {candidate_profile.basic.desired_industry if candidate_profile.basic and candidate_profile.basic.desired_industry else "정보 없음"}
- 희망 회사규모: {candidate_profile.basic.desired_company_size if candidate_profile.basic and candidate_profile.basic.desired_company_size else "정보 없음"}
- 거주지: {candidate_profile.basic.residence_location if candidate_profile.basic and candidate_profile.basic.residence_location else "정보 없음"}
- 희망 근무지: {candidate_profile.basic.desired_work_location if candidate_profile.basic and candidate_profile.basic.desired_work_location else "정보 없음"}

## 경력 사항
{experience_summary}

## 학력
{education_summary}

## 활동 (프로젝트, 오픈소스, 동아리 등)
{activity_summary}

## 자격증
{certification_summary}

## 구조화 면접 분석
- 주요 테마: {", ".join(general_analysis.key_themes)}
- 관심 분야: {", ".join(general_analysis.interests)}
- 강조한 경험: {", ".join(general_analysis.emphasized_experiences)}
- 업무 스타일: {", ".join(general_analysis.work_style_hints)}
- 기술 키워드: {", ".join(general_analysis.technical_keywords)}

## 직무 적합성 면접 분석
- 평가된 기술: {", ".join(technical_analysis.evaluated_skills)}
- 강한 영역: {", ".join(technical_analysis.strong_areas)}
- 사용 도구/프레임워크: {", ".join(technical_analysis.mentioned_tools)}
- 프로젝트 하이라이트: {", ".join(technical_analysis.project_highlights)}
- 깊이있게 다룬 영역: {", ".join(technical_analysis.technical_depth)}

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
    technical_analysis: TechnicalInterviewAnalysis,
    situational_report: FinalPersonaReport
) -> dict:
    """
    인재의 면접 결과로부터 6가지 매칭 벡터 생성 (텍스트 생성 + 임베딩)

    Args:
        candidate_profile: 지원자 기본 프로필
        general_analysis: 구조화 면접 분석
        technical_analysis: 직무 적합성 면접 분석
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
        technical_analysis=technical_analysis,
        situational_report=situational_report
    )

    # 2. 생성된 텍스트 출력
    print("\n" + "="*80)
    print("📝 생성된 매칭 텍스트")
    print("="*80)
    print("\n[1] 역할 적합도/역할 수행력")
    print("-"*80)
    print(texts.roles_text)
    print("\n[2] 역량 적합도")
    print("-"*80)
    print(texts.skills_text)
    print("\n[3] 성장 기회 제공/성장 가능성")
    print("-"*80)
    print(texts.growth_text)
    print("\n[4] 커리어 방향")
    print("-"*80)
    print(texts.career_text)
    print("\n[5] 비전 신뢰도/협업 기여도")
    print("-"*80)
    print(texts.vision_text)
    print("\n[6] 조직/문화 적합도")
    print("-"*80)
    print(texts.culture_text)
    print("="*80 + "\n")

    # 3. 텍스트를 벡터로 임베딩
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

