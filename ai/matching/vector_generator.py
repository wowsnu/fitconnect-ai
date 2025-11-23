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
    FinalPersonaReport,
    CandidateProfileCard,
    CompetencyItem
)
from config.settings import get_settings


class ProfileBasedCard(BaseModel):
    """프로필 기반 카드 생성 결과"""

    key_experiences: list[str] = Field(
        description="주요 경험/경력 (4개)",
        min_length=4,
        max_length=4
    )

    strengths: list[str] = Field(
        description="강점 (4개)",
        min_length=4,
        max_length=4
    )

    core_competencies: list[CompetencyItem] = Field(
        description="핵심 일반 역량 (4개)",
        min_length=4,
        max_length=4
    )

    technical_skills: list[CompetencyItem] = Field(
        description="핵심 직무 역량/기술 (4개)",
        min_length=4,
        max_length=4
    )

    job_fit: str = Field(description="직무 적합성 요약 (2-3문장)")
    team_fit: str = Field(description="협업 성향 요약 (2-3문장)")
    growth_potential: str = Field(description="성장 가능성 요약 (2-3문장)")


class TalentMatchingTexts(BaseModel):
    """인재 매칭용 6가지 텍스트"""

    roles_text: str = Field(
        description="역할 적합도/역할 수행력 텍스트",
        min_length=100,
        max_length=700
    )

    skills_text: str = Field(
        description="역량 적합도 텍스트",
        min_length=100,
        max_length=700
    )

    growth_text: str = Field(
        description="성장 기회 제공/성장 가능성 텍스트",
        min_length=100,
        max_length=700
    )

    career_text: str = Field(
        description="커리어 방향 텍스트",
        min_length=100,
        max_length=700
    )

    vision_text: str = Field(
        description="비전 신뢰도/협업 기여도 텍스트",
        min_length=100,
        max_length=700
    )

    culture_text: str = Field(
        description="조직/문화 적합도 텍스트",
        min_length=100,
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
        ("system", """당신은 채용 매칭 전문가입니다.

인재의 면접 결과를 바탕으로, 기업과의 매칭을 위한 **6가지 텍스트**를 생성하세요.

---

## 핵심 작성 원칙

### 1. 쉬운 말로 쓰기
- 전문용어나 어려운 단어 대신 **일상적인 표현** 사용
- 예시:
  - ❌ "크로스펑셔널 협업 역량" → ✅ "여러 팀과 함께 일한 경험"
  - ❌ "아키텍처 설계 능력" → ✅ "전체 구조를 설계한 경험"
  - ❌ "스토리텔링 구현 역량" → ✅ "이야기를 영상으로 풀어낸 경험"

### 2. 도구보다 '뭘 할 수 있는지' 강조
- 도구 이름만 나열하지 말고, **그걸로 뭘 했는지** 설명
- 예시:
  - ❌ "Premiere Pro 능숙" → ✅ "영상 편집 경험이 많음 (Premiere Pro 사용)"
  - ❌ "Python 가능" → ✅ "데이터 분석 경험 있음 (Python 사용)"
  - ❌ "Figma 사용" → ✅ "화면 설계와 디자인 경험 있음 (Figma 사용)"

### 3. 경험 수준을 솔직하게
- 경력에 맞는 표현 사용 (과장하거나 축소하지 않기)
- **경험 적음 (0-2년)**: "배우는 중", "경험 시작", "참여해봤다", "해본 적 있다"
- **경험 있음 (3-5년)**: "혼자서도 할 수 있다", "담당했다", "직접 만들었다"
- **경험 많음 (6년+)**: "팀을 이끌었다", "전체를 책임졌다", "후배를 가르쳤다"

### 4. 성격/성향은 구체적으로
- 모호한 표현 대신 **어떤 상황에서 어떻게 행동하는지** 설명
- 예시:
  - ❌ "협업을 좋아함" → ✅ "다른 팀 사람들과 자주 대화하며 일하는 걸 좋아함"
  - ❌ "꼼꼼한 편" → ✅ "마감 전에 여러 번 확인하고, 체크리스트를 만들어 씀"
  - ❌ "도전적" → ✅ "안 해본 일도 일단 해보려고 하는 편"

---

## 텍스트별 작성 가이드 (각 500-700자)

### 1. 역할 수행력 (roles_text)
**이 사람이 어떤 일을 해봤는지**
- 몇 년 동안 어떤 일을 했는지
- 어떤 프로젝트에서 어떤 역할을 맡았는지
- 실제로 만들어낸 결과물이 뭔지
- 일하면서 어떤 어려움이 있었고 어떻게 해결했는지

### 2. 역량 (skills_text)
**이 사람이 뭘 잘하는지**
- 잘하는 기술이나 능력 (도구 이름 + 그걸로 뭘 했는지)
- 사람들과 일할 때의 강점
- 실제 경험에서 검증된 능력

### 3. 성장 가능성 (growth_text)
**이 사람이 앞으로 얼마나 성장할 수 있을지**
- 새로운 걸 배울 때 어떻게 하는지
- 모르는 분야를 접했을 때 어떻게 대처하는지
- 스스로 공부하거나 연습한 경험이 있는지
- 앞으로 더 잘하고 싶은 분야가 뭔지

### 4. 커리어 방향 (career_text)
**이 사람이 앞으로 어떤 일을 하고 싶은지**
- 지금까지 어떤 길을 걸어왔는지
- 앞으로 어떤 일을 하고 싶은지
- 왜 그 방향을 선택했는지
- 그걸 위해 뭘 준비하고 있는지

### 5. 협업 성향 (vision_text)
**이 사람이 팀에서 어떻게 일하는지**
- 다른 사람들과 어떻게 소통하는지
- 팀에서 어떤 역할을 맡는 편인지
- 의견이 다를 때 어떻게 하는지
- 함께 일하면서 겪은 어려움과 해결 방법

### 6. 문화 적합도 (culture_text)
**이 사람이 어떤 환경에서 잘 맞는지**
- 일할 때의 스타일 (혼자 vs 같이, 꼼꼼 vs 빠르게)
- 문제가 생겼을 때 어떻게 접근하는지
- 어떤 분위기의 회사를 원하는지
- 바쁘거나 힘들 때 어떻게 대처하는지

---

**중요**:
- 각 텍스트 **500-700자**
- 면접에서 나온 **실제 이야기**만 사용 (추측 금지)
- **전문용어 쓰지 않기** - 일반인이 읽어도 이해되게
- 경험 수준을 솔직하게 (경험 많으면 많다고, 적으면 적다고)
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


def generate_card_from_profile_only(
    candidate_profile: CandidateProfile
) -> CandidateProfileCard:
    """
    프로필 정보만으로 인재 카드 생성 (인터뷰 없이)

    Args:
        candidate_profile: 지원자 프로필

    Returns:
        CandidateProfileCard
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
        ("system", """당신은 HR 채용 전문가입니다.

지원자의 프로필 정보를 분석하여 인재 카드를 생성하세요.

**생성 항목:**
1. **key_experiences**: 주요 경험/경력 (4개) - 가장 인상적인 경력 4가지
2. **strengths**: 강점 (4개) - 프로필에서 드러나는 강점
3. **core_competencies**: 핵심 일반 역량 (4개) - 이름과 수준(높음/보통/낮음)
4. **technical_skills**: 핵심 직무 역량/기술 (4개) - 이름과 수준(높음/보통/낮음)
5. **job_fit**: 직무 적합성 요약 (2-3문장)
6. **team_fit**: 협업 성향 요약 (2-3문장)
7. **growth_potential**: 성장 가능성 요약 (2-3문장)

**작성 원칙:**
- 프로필에 있는 정보만 사용 (추측 금지)
- 경력, 학력, 활동, 자격증을 종합적으로 분석
- 구체적이고 명확한 표현 사용
- 수준은 경력 연차와 경험을 기반으로 판단
"""),
        ("user", f"""## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 한줄소개: {candidate_profile.basic.tagline if candidate_profile.basic and candidate_profile.basic.tagline else "없음"}
- 총 경력: {sum((exp.duration_years or 0) for exp in candidate_profile.experiences)}년

## 희망 조건
- 희망 직무: {candidate_profile.basic.desired_role if candidate_profile.basic and candidate_profile.basic.desired_role else "정보 없음"}
- 희망 산업: {candidate_profile.basic.desired_industry if candidate_profile.basic and candidate_profile.basic.desired_industry else "정보 없음"}

## 경력 사항
{experience_summary}

## 학력
{education_summary}

## 활동 (프로젝트, 오픈소스, 동아리 등)
{activity_summary}

## 자격증
{certification_summary}

위 정보를 바탕으로 인재 카드를 생성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(ProfileBasedCard)

    result = (prompt | llm).invoke({})

    # ProfileBasedCard를 CandidateProfileCard로 변환
    candidate_name = candidate_profile.basic.name if candidate_profile.basic else "지원자"

    if candidate_profile.basic and candidate_profile.basic.tagline:
        role = candidate_profile.basic.tagline
    elif candidate_profile.experiences:
        role = candidate_profile.experiences[0].title
    else:
        role = "개발자"

    experience_years = sum((exp.duration_years or 0) for exp in candidate_profile.experiences)
    company = candidate_profile.experiences[0].company_name if candidate_profile.experiences else ""

    return CandidateProfileCard(
        candidate_name=candidate_name,
        role=role,
        experience_years=experience_years,
        company=company,
        key_experiences=result.key_experiences,
        strengths=result.strengths,
        core_competencies=result.core_competencies,
        technical_skills=result.technical_skills,
        job_fit=result.job_fit,
        team_fit=result.team_fit,
        growth_potential=result.growth_potential
    )


class ProfileBasedMatchingTexts(BaseModel):
    """프로필 기반 매칭 텍스트"""

    roles_text: str = Field(description="역할 적합도 텍스트", min_length=100, max_length=700)
    skills_text: str = Field(description="역량 적합도 텍스트", min_length=100, max_length=700)
    growth_text: str = Field(description="성장 가능성 텍스트", min_length=100, max_length=700)
    career_text: str = Field(description="커리어 방향 텍스트", min_length=100, max_length=700)
    vision_text: str = Field(description="협업 기여도 텍스트", min_length=100, max_length=700)
    culture_text: str = Field(description="문화 적합도 텍스트", min_length=100, max_length=700)


def generate_vectors_from_profile_only(
    candidate_profile: CandidateProfile
) -> dict:
    """
    프로필 정보만으로 매칭 벡터 생성 (인터뷰 없이)

    Args:
        candidate_profile: 지원자 프로필

    Returns:
        {
            "texts": {매칭 텍스트 6개},
            "vectors": {벡터 6개},
            "card": CandidateProfileCard
        }
    """
    from ai.matching.embedding import embed_matching_texts

    print("[ProfileOnly] Generating card and vectors from profile...")

    # 1. 카드 생성
    card = generate_card_from_profile_only(candidate_profile)
    print(f"[ProfileOnly] Card generated for {card.candidate_name}")

    # 2. 매칭 텍스트 생성
    experience_summary = "\n".join([
        f"- {exp.company_name} / {exp.title} ({exp.duration_years or 0}년)" +
        (f"\n  요약: {exp.summary}" if exp.summary else "")
        for exp in candidate_profile.experiences
    ]) if candidate_profile.experiences else "경력 없음"

    activity_summary = "\n".join([
        f"- {act.name}" +
        (f" ({act.category})" if act.category else "") +
        (f": {act.description}" if act.description else "")
        for act in candidate_profile.activities
    ]) if candidate_profile.activities else "활동 정보 없음"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 매칭 전문가입니다.

인재의 프로필 정보를 바탕으로 기업과의 매칭을 위한 **6가지 텍스트**를 생성하세요.

---

## 핵심 작성 원칙

### 1. 쉬운 말로 쓰기
- 전문용어 대신 **일상적인 표현** 사용
- 예시:
  - ❌ "크로스펑셔널 협업 역량" → ✅ "여러 팀과 함께 일한 경험"
  - ❌ "아키텍처 설계" → ✅ "전체 구조를 설계한 경험"

### 2. 도구보다 '뭘 할 수 있는지' 강조
- 도구 이름만 나열하지 말고, **그걸로 뭘 했는지** 설명
- 예시:
  - ❌ "Premiere Pro 능숙" → ✅ "영상 편집 경험이 많음 (Premiere Pro 사용)"
  - ❌ "Python 가능" → ✅ "데이터 분석 경험 있음 (Python 사용)"

### 3. 경험 수준을 솔직하게
- **경험 적음 (0-2년)**: "배우는 중", "참여해봤다", "해본 적 있다"
- **경험 있음 (3-5년)**: "혼자서도 할 수 있다", "담당했다", "직접 만들었다"
- **경험 많음 (6년+)**: "팀을 이끌었다", "전체를 책임졌다"

### 4. 성격/성향은 구체적으로
- 예시:
  - ❌ "협업을 좋아함" → ✅ "다른 팀 사람들과 자주 대화하며 일하는 걸 좋아함"
  - ❌ "꼼꼼한 편" → ✅ "마감 전에 여러 번 확인하고, 체크리스트를 만들어 씀"

---

## 텍스트별 작성 가이드 (각 500-700자)

### 1. 역할 수행력 (roles_text)
**이 사람이 어떤 일을 해봤는지**
- 몇 년 동안 어떤 일을 했는지
- 어떤 프로젝트에서 어떤 역할을 맡았는지
- 실제로 만들어낸 결과물이 뭔지

### 2. 역량 (skills_text)
**이 사람이 뭘 잘하는지**
- 잘하는 기술이나 능력 (도구 이름 + 그걸로 뭘 했는지)
- 사람들과 일할 때의 강점

### 3. 성장 가능성 (growth_text)
**이 사람이 앞으로 얼마나 성장할 수 있을지**
- 새로운 걸 배울 때 어떻게 하는지
- 스스로 공부하거나 연습한 경험

### 4. 커리어 방향 (career_text)
**이 사람이 앞으로 어떤 일을 하고 싶은지**
- 지금까지 어떤 길을 걸어왔는지
- 앞으로 어떤 일을 하고 싶은지

### 5. 협업 성향 (vision_text)
**이 사람이 팀에서 어떻게 일하는지**
- 다른 사람들과 어떻게 소통하는지
- 팀에서 어떤 역할을 맡는 편인지

### 6. 문화 적합도 (culture_text)
**이 사람이 어떤 환경에서 잘 맞는지**
- 일할 때의 스타일 (혼자 vs 같이, 꼼꼼 vs 빠르게)
- 어떤 분위기의 회사를 원하는지

---

**중요**:
- 각 텍스트 **500-700자**
- **전문용어 쓰지 않기** - 일반인이 읽어도 이해되게
- 프로필 정보가 부족해도 있는 정보를 최대한 활용
"""),
        ("user", f"""## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 한줄소개: {candidate_profile.basic.tagline if candidate_profile.basic and candidate_profile.basic.tagline else "없음"}
- 총 경력: {sum((exp.duration_years or 0) for exp in candidate_profile.experiences)}년

## 희망 조건
- 희망 직무: {candidate_profile.basic.desired_role if candidate_profile.basic and candidate_profile.basic.desired_role else "정보 없음"}
- 희망 산업: {candidate_profile.basic.desired_industry if candidate_profile.basic and candidate_profile.basic.desired_industry else "정보 없음"}
- 희망 회사규모: {candidate_profile.basic.desired_company_size if candidate_profile.basic and candidate_profile.basic.desired_company_size else "정보 없음"}
- 희망 근무지: {candidate_profile.basic.desired_work_location if candidate_profile.basic and candidate_profile.basic.desired_work_location else "정보 없음"}

## 경력 사항
{experience_summary}

## 활동
{activity_summary}

## 생성된 카드 정보
- 주요 경험: {', '.join(card.key_experiences)}
- 강점: {', '.join(card.strengths)}
- 일반 역량: {', '.join([f"{c.name}({c.level})" for c in card.core_competencies])}
- 기술 역량: {', '.join([f"{c.name}({c.level})" for c in card.technical_skills])}
- 직무 적합성: {card.job_fit}
- 협업 성향: {card.team_fit}
- 성장 가능성: {card.growth_potential}

위 정보를 바탕으로 6가지 매칭 텍스트를 생성하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(ProfileBasedMatchingTexts)

    texts = (prompt | llm).invoke({})
    print("[ProfileOnly] Matching texts generated")

    # 3. 텍스트를 벡터로 임베딩
    vectors = embed_matching_texts(
        roles_text=texts.roles_text,
        skills_text=texts.skills_text,
        growth_text=texts.growth_text,
        career_text=texts.career_text,
        vision_text=texts.vision_text,
        culture_text=texts.culture_text
    )
    print("[ProfileOnly] Vectors embedded")

    return {
        "card": card,
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
