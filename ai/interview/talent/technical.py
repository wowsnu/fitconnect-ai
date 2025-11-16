"""
Technical Interview (직무 적합성 면접)

- 기본: 4개 기술 × 2질문 = 8개 질문 (설정 가능)
- 구조화 면접 분석 결과 활용
- 개인화된 질문 생성
- 이전 답변 기반으로 자연스럽게 깊이 파고들기
- 점수 없음, 피드백만
"""

from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ai.interview.talent.models import (
    CandidateProfile,
    GeneralInterviewAnalysis,
    TechnicalInterviewAnalysis,
    InterviewQuestion,
    AnswerFeedback,
    TechnicalInterviewCardPart,
)
from config.settings import get_settings


def _format_question_list(all_questions: List[dict], limit: int = 7) -> str:
    """프롬프트용 간단 질문 목록"""
    if not all_questions:
        return "없음"

    lines: List[str] = []
    for item in all_questions[-limit:]:
        question = (item.get("question") or "").strip()
        skill = item.get("skill") or ""
        skill_label = f"[기술: {skill}]" if skill else "[기술 정보 없음]"
        qnum = item.get("question_number")
        if qnum:
            skill_label += f" Q{qnum}"
        lines.append(f"- {skill_label} {question}")
    return "\n".join(lines)


class TechnicalSkillSelection(BaseModel):
    """LLM structured output for 기술 선정"""
    skills: List[str] = Field(
        ...,
        min_length=1,
        description="중복 없는 기술/역량 키워드 목록"
    )


def generate_personalized_question(
    skill: str,
    question_number: int,
    profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    previous_skill_answers: List[dict] = None,
    all_previous_questions: List[dict] = None,
    use_langgraph_for_questions: Optional[bool] = None
) -> InterviewQuestion:
    """프로필과 기존 질문 목록을 활용한 개인화 질문 생성"""
    settings = get_settings()
    previous_skill_answers = previous_skill_answers or []
    all_previous_questions = all_previous_questions or []
    use_langgraph = (
        use_langgraph_for_questions
        if use_langgraph_for_questions is not None
        else settings.USE_LANGGRAPH_FOR_QUESTIONS
    )

    if use_langgraph:
        from ai.interview.talent.technical_graph import generate_personalized_question_with_graph

        return generate_personalized_question_with_graph(
            skill=skill,
            question_number=question_number,
            profile=profile,
            general_analysis=general_analysis,
            previous_skill_answers=previous_skill_answers,
            all_previous_questions=all_previous_questions,
        )

    prev_context = ""
    if previous_skill_answers:
        prev_context = "\n\n**이전 질문과 답변:**\n"
        for i, ans in enumerate(previous_skill_answers, 1):
            prev_context += f"\n[질문 {i}] {ans['question']}\n"
            prev_context += f"[답변] {ans['answer']}\n"
            if ans.get('feedback'):
                depth_areas = ans['feedback'].get('depth_areas', [])
                if depth_areas:
                    prev_context += f"[파고들 포인트] {', '.join(depth_areas)}\n"

    question_list_text = _format_question_list(all_previous_questions)

    if question_number == 1:
        depth_guide = """**1번째 질문 (도입):**
- 구조화 면접에서 언급한 핵심 주제나 관심사를 자연스럽게 연결
- 예1: "아까 데이터 기반 의사결정에 관심이 많다고 하셨는데, 실제로 어떤 경험이 있었나요?"
- 예2: "디자인 프로젝트에서 사용자 피드백을 반영했다고 하셨는데, 구체적으로 어떤 과정을 거치셨나요?"
- 지원자의 전반적인 역할, 경험에 대한 동기와 과정 탐색
"""
    else:
        depth_guide = """**2번째 질문 (심화):**
- 1번째 답변의 경험을 더 깊이 탐구하고, 사고의 깊이와 확장성 파악
- 단순한 사례 회고가 아니라, '그 경험을 통해 무엇을 배웠고 이후 어떻게 적용했는가'를 끌어내는 단계
- 예1: 1번에서 "마케팅 캠페인 성과 분석"을 언급했다면 → "성과 측정 시 어떤 지표나 도구를 활용하셨나요?"
- 예2: "그 경험을 통해 얻은 교훈이나 인사이트를 이후 다른 프로젝트에 어떻게 적용하셨나요?"
- 예3: "만약 같은 상황이 다시 온다면, 어떤 부분을 다르게 접근하고 싶으신가요?"
- 예4: "그 접근법을 선택한 이유가 있나요? 다른 아키텍처는 고려하지 않으셨나요?"
- 목표: 지원자의 사고 수준, 성장 가능성, 문제 재구조화 능력 파악
- 실무 적용 과정, 문제 해결 접근법, 의사결정 근거 파악
"""

    job_category = profile.basic.tagline if profile.basic else ""

    skills: List[str] = []
    for exp in profile.experiences:
        if exp.summary:
            skills.extend([kw.strip() for kw in exp.summary.split(',') if kw.strip()])

    unique_skills = sorted({skill for skill in skills if skill})
    skills = unique_skills[:10]

    total_experience = sum((exp.duration_years or 0) for exp in profile.experiences)

    experience_entries = []
    for exp in profile.experiences:
        duration_text = f"{exp.duration_years}년" if exp.duration_years is not None else "기간 정보 없음"
        experience_entries.append(f"- {exp.company_name} / {exp.title} ({duration_text})")
    experience_summary = "\n".join(experience_entries)

    activities_summary = "\n".join([
        f"- {act.name} ({act.category}): {act.description or ''}"
        for act in profile.activities
    ])

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 {job_category} 직군의 실무진(직무 적합성 면접) 면접관으로,
        지원자의 프로필과 이전 질문 목록을 참고하여, 직무 역량을 검증하기 위한 열린 면접 질문을 만들어 주세요.

        **지원자 프로필:**
        - 이름: {profile.basic.name if profile.basic else "지원자"}
        - 직무: {job_category}
        - 총 경력: {total_experience}년

        **경력사항:**
        {experience_summary}

        **활동/프로젝트:**
        {activities_summary}

        **추출된 기술 키워드:**
        {", ".join(skills) if skills else "정보 없음"}

        **구조화 면접에서 파악된 특성:**
        - 주요 테마: {", ".join(general_analysis.key_themes)}
        - 관심 분야: {", ".join(general_analysis.interests)}
        - 강조한 경험: {", ".join(general_analysis.emphasized_experiences)}
        - 업무 스타일: {", ".join(general_analysis.work_style_hints)}
        - 언급한 기술: {", ".join(general_analysis.technical_keywords)}

        **질문 생성 방법:**
        - **직무 역량 선정** : 지원자의 직무에 적합하고 필요한 역량을 6개 선정
        - **역량 수준 체계** 정의 : 각 역량마다 역량 수준 체계(low/medium/high)을 구체적인 기준으로 제시
        - **수준 체계 기반 질문 생성** : 역량 수준 체계를 참고하여 평가 가능하도록 적절한 질문을 생성

        **질문 생성 전략:**
        {depth_guide}

        **번호 규칙:**
        - question_number는 해당 기술 내 순번 (1=도입, 2=심화)입니다.

        **질문 원칙:**
        - 열린 질문 (지원자가 실제 경험을 말할 수 있도록 유도, 실무 중심의 구체적인 질문)
        - 사실 기반 질문 (프로필과 인터뷰 답변에 있는 내용만 사용하여 적절한 질문 생성, 제시되지 않은 경험을 만들어서 물어보지 말 것)
        - 추정 및 과장 금지 (언급되지 않은 내용을 만들어내지 말 것)
        - 유사 질문 금지 (의미없이 비슷한 질문을 하는 것은 지양)
        - 추가 질문일 경우 이전 답변에서 언급된 내용을 바탕으로 더 구체적이고 깊이 있는 후속 질문을 생성
        - **질문 길이는 130자 이내로 간결하게 작성**
        - 아래 질문 목록(이미 사용한 질문)과 동일/유사한 질문을 반복하지 말 것
       
        **예시:**
        - 새로운 교육 프로그램을 설계할 때, 학습자 요구나 조직의 목표를 어떻게 반영하셨나요? 설계 과정에서 어떤 의사결정을 내렸는지 구체적으로 말씀해 주세요.
        - 이전 답변에서 React 프로젝트를 진행하며 Redux를 사용했다고 답하셨는데, Redux를 선택한 이유는 무엇인가요? 그 선택이 프로젝트 구조나 성능에 어떤 영향을 주었는지도 설명해 주세요.
        """),
        ("user", f"""
현재 평가 기술: {skill}
질문 번호: {question_number}/3
{prev_context}

**지금까지 사용한 질문 목록(최대 6개, 이미 진행한 질문입니다 / Qn은 해당 기술 내 순번):**
{question_list_text}
→ 위 질문을 반복하지 말고 새로운 각도의 질문을 생성하세요.

{skill}에 대한 {question_number}번째 질문을 생성하세요.
""")
    ])

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(InterviewQuestion)

    return (prompt | llm).invoke({})


def analyze_answer(
    question: str,
    answer: str,
    skill: str
) -> AnswerFeedback:
    """
    답변 분석 (점수 없음, 피드백만)

    Args:
        question: 질문
        answer: 답변
        skill: 기술

    Returns:
        AnswerFeedback
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 {skill} 직군의 실무진(직무 적합성 면접) 면접관입니다.

        답변을 분석하여 다음 질문을 위한 인사이트를 제공하세요.

        **분석 목표:**
        1. 답변에서 언급된 주요 포인트 추출
        2. 사용한 방법, 접근 방식, 도구 등 업무 수행 요소 파악
        3. 더 깊이 파고들 수 있는 영역 식별
        4. 다음 질문에서 집중해야 할 방향 제시

        **중요:**
        - 점수를 매기지 마세요
        - 다음 질문이 무엇을 집중해야 할지 명확히 제시
        - 답변에서 애매하거나 더 알아볼 부분 찾기
        - 강점과 직무 역량이 명확히 드러나도록 분석
        - 이전 질문에서 물어본 내용을 반복해서 물어보지 않도록 주의
        """),
                ("user", f"""
        질문: {question}
        답변: {answer}

        답변을 분석하고 피드백을 제공하세요.
        """)
            ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(AnswerFeedback)

    return (prompt | llm).invoke({})


def analyze_technical_interview(technical_results: dict) -> TechnicalInterviewAnalysis:
    """
    직무 적합성 면접 답변들을 종합 분석 (벡터 생성용)

    Args:
        technical_results: 직무 면접 결과
            {
                "skills_evaluated": List[str],
                "results": {skill: [{"question": str, "answer": str, "feedback": dict}, ...]},
                "total_questions": int
            }

    Returns:
        TechnicalInterviewAnalysis
    """
    skills_evaluated = technical_results.get("skills_evaluated", [])
    results = technical_results.get("results", {})

    # 모든 Q&A를 하나의 텍스트로 결합
    all_qa = []
    for skill, questions in results.items():
        all_qa.append(f"\n[{skill}]")
        for q in questions:
            all_qa.append(f"Q: {q['question']}")
            all_qa.append(f"A: {q['answer']}")
            # 피드백도 포함
            if q.get('feedback'):
                feedback = q['feedback']
                if feedback.get('mentioned_technologies'):
                    all_qa.append(f"언급 기술: {', '.join(feedback['mentioned_technologies'])}")

    all_qa_text = "\n".join(all_qa)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 전문가입니다.

        직무 적합성 면접 답변들을 분석하여, 인재-기업 매칭을 위한 핵심 정보를 추출하세요.

        **분석 목표:**
        1. 평가된 직무 역량 목록 (면접에서 드러난 업무 수행 능력, 전문 지식, 의사결정 역량 등)
        2. 강하게 드러난 핵심 영역 (깊이 있는 이해, 실무 경험 풍부, 전략적 판단 등)
        3. 답변에서 언급된 방법, 도구, 프로세스 또는 접근 방식
        4. 주요 프로젝트/업무 경험 하이라이트 (구체적 성과, 기억에 남는 경험)
        5. 깊이 있게 다룬 영역 (문제 해결, 의사결정 과정, 최적화, 개선, 전략 설계 등)

        **중요:**
        - 사실 기반 평가: 프로필과 면접 답변에 나타난 내용만 사용, 면접 질문 자체는 포함하지 않음
        - 추정 및 과장 금지: 언급되지 않은 내용을 만들어내지 않음
        - 행동 및 경험 기반 평가: 실제 드러난 행동, 의사결정, 업무 수행 과정에 집중하여 분석
        - 종합적 해석과 구체적 서술: 답변의 핵심을 명확한 키워드와 사례 중심으로 간단히 정리
        - 과대/과소 평가 금지: 답변 내용이 부족할 경우, 적절히 낮게 평가 가능
        """),
                ("user", f"""
        ## 평가된 기술
        {', '.join(skills_evaluated)}

        ## 면접 Q&A
        {all_qa_text}

        위 정보를 바탕으로 5가지 항목을 추출하세요.
        """)
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TechnicalInterviewAnalysis)

    return (prompt | llm).invoke({})


def analyze_technical_interview_for_card(
    candidate_profile: CandidateProfile,
    technical_results: dict
) -> TechnicalInterviewCardPart:
    """
    직무 면접 결과를 프로필 카드용 파트로 변환

    Args:
        candidate_profile: 지원자 기본 프로필
        technical_results: 직무 면접 결과

    Returns:
        TechnicalInterviewCardPart
    """
    skills_evaluated = technical_results.get("skills_evaluated", [])
    results = technical_results.get("results", {})

    qa_summary: list[str] = []
    for skill, questions in results.items():
        qa_summary.append(f"\n[{skill}]")
        for q in questions:
            qa_summary.append(f"Q: {q['question'][:100]}...")
            qa_summary.append(f"A: {q['answer'][:150]}...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 채용 전문가입니다.
         
        직무적합성 면접 결과를 분석하여 **강점**과 **핵심 직무 역량/기술**을 추출하세요.

        **추출 목표:**

        1. **강점 (4개)**:
        - 업무 수행 시 돋보이는 강점
        - 실제 면접 답변에서 드러난 행동, 사고방식, 문제 해결 능력 중심
        - 예: "빠른 학습 능력과 적응력", "체계적인 문제 해결 접근", "팀 내 협업 및 조율 능력"

        2. **핵심 직무 역량 (4개)**:
        - 업무 수행에 필요한 전문 지식, 기술 스택 (기술 직군), 방법론, 프로세스, 접근 방식 등
        - 각 역량의 수준: "높음", "보통", "낮음"
        - 면접에서 드러난 경험과 구체적 사례 기반
        - 예시: name에 교육 프로그램 설계 역량과 같은 역량명, level에 높음/보통/낮음 중 하나 
 
        **레벨 판단 기준:**
        - **높음**: 깊이 있는 이해, 실제 사례·성과로 입증, 전략적 판단이나 문제 해결 경험 포함
        - **보통**: 기본적 이해와 일부 경험 존재, 제한적 사례
        - **낮음**: 개념 수준에 그치거나 경험 근거 부족

        **판단 과정:**
        - **역량 단서 탐색 및 역량 선정** : 면접 답변에서 반복적으로 드러나는 태도, 행동 패턴, 언어 표현을 바탕으로 역량 도출  
        - **맥락 분석 및 증거 수집** : 해당 역량이 드러난 구체적인 상황이나 사례를 추출, 단순 언급인지 혹은 실제 행동이나 성과로 이어졌는지를 구분  
        - **레벨 판단** : 역량마다 레벨에 대한 구체적인 정의를 내리고, 면접 답변을 바탕으로 레벨을 세밀하고 객관적으로 평가

        **분석 원칙:**
        - 사실 기반 평가: 프로필과 면접 답변에 나타난 내용만 사용
        - 추정 및 과장 금지: 언급되지 않은 내용을 만들어내지 않음
        - 행동 및 경험 기반 평가: 실제 드러난 행동, 의사결정, 업무 수행 과정 중심
        - 종합적 해석과 구체적 서술: 핵심 키워드와 사례 중심으로 정리
        - 과대/과소 평가 금지: 답변 내용이 부실할 경우, 적절히 낮게 평가 가능
        - 전 직군 적용 가능: 기술, 기획, 디자인, 마케팅, HR 등 모든 직무에 적용
        """),
        ("user", f"""
## 지원자 기본 정보
- 이름: {candidate_profile.basic.name if candidate_profile.basic else "지원자"}
- 직무: {candidate_profile.basic.tagline if candidate_profile.basic else ""}
- 기술 스택: {', '.join([exp.summary or '' for exp in candidate_profile.experiences if exp.summary])}

## 직무적합성 면접 결과
- 평가된 기술: {', '.join(skills_evaluated)}

## 질문/답변 요약
{chr(10).join(qa_summary)}

위 정보를 바탕으로 **강점 4개**와 **핵심 직무 역량/기술 4개**를 추출하세요.
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TechnicalInterviewCardPart)

    return (prompt | llm).invoke({})


class TechnicalInterview:
    """직무 적합성 면접 관리 클래스"""

    def __init__(
        self,
        profile: CandidateProfile,
        general_analysis: GeneralInterviewAnalysis,
        num_skills: int = 3,
        questions_per_skill: int = 3,
        use_langgraph_for_questions: Optional[bool] = None
    ):
        """
        Args:
            profile: 지원자 프로필
            general_analysis: 구조화 면접 분석 결과
            num_skills: 평가할 기술 개수 (기본 3개)
            questions_per_skill: 기술당 질문 수 (기본 3개)
        """
        settings = get_settings()
        self.profile = profile
        self.general_analysis = general_analysis
        self.questions_per_skill = questions_per_skill
        self.use_langgraph_for_questions = (
            use_langgraph_for_questions
            if use_langgraph_for_questions is not None
            else settings.USE_LANGGRAPH_FOR_QUESTIONS
        )

        # 평가할 기술 선정
        self.skills = self._select_skills(num_skills)

        # 상태 관리
        self.current_skill_idx = 0
        self.current_question_num = 1  # 1, 2, 3

        # 결과 저장
        self.results = {skill: [] for skill in self.skills}
        self.current_question = None

    def _select_skills(self, num_skills: int) -> List[str]:
        """LLM 기반 기술 선정 (휴리스틱 보조)"""
        llm_skills = self._select_skills_with_llm(num_skills)
        fallback_skills = self._select_skills_fallback(num_skills)

        merged: List[str] = []
        for skill in llm_skills + fallback_skills:
            normalized = (skill or "").strip()
            if not normalized:
                continue
            if normalized not in merged:
                merged.append(normalized)
            if len(merged) >= num_skills:
                break

        if not merged:
            merged = fallback_skills[:num_skills]

        return merged[:num_skills]

    def _select_skills_with_llm(self, num_skills: int) -> List[str]:
        """LLM에게 기술 선정 위임"""
        if num_skills <= 0:
            return []

        job_category = self.profile.basic.tagline if self.profile.basic else ""
        experience_entries = []
        for exp in self.profile.experiences:
            duration_text = f"{exp.duration_years}년" if exp.duration_years is not None else "기간 정보 없음"
            summary = exp.summary or ""
            entry = f"- {exp.company_name} / {exp.title} ({duration_text}) {summary}"
            experience_entries.append(entry.strip())
        experience_summary = "\n".join(experience_entries) or "경력 정보 없음"

        analysis_summary = f"""
주요 테마: {', '.join(self.general_analysis.key_themes)}
관심 분야: {', '.join(self.general_analysis.interests)}
강조 경험: {', '.join(self.general_analysis.emphasized_experiences)}
언급 기술: {', '.join(self.general_analysis.technical_keywords)}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 채용 인터뷰 설계 전문가입니다.
지원자의 프로필과 구조화 면접 분석을 토대로, 직무 적합성을 검증할 기술/역량 키워드를 선정하세요.

선정 기준:
1. 구조화 면접에서 언급되고 프로필에도 나타난 기술(교집합)을 최우선으로 포함
2. 면접에서만 언급된 기술 (중요도가 높음)
3. 프로필에서만 확인되는 기술이나 역할
4. 위 기준으로 부족하면 interests, emphasized_experiences, 직무명 등을 활용
5. 모든 항목은 중복 없이 구체적인 기술/역량 명칭일 것

반드시 {num_skills}개를 반환하세요. 없으면 가장 관련성 높은 역량으로 채우세요."""),
            ("user", f"""
지원자 직무: {job_category or '정보 없음'}

## 경력 요약
{experience_summary}

## 구조화 면접 분석
{analysis_summary}

LLM이 직접 기술 목록을 선정하고, JSON이 아닌 구조화 출력으로 반환하세요.
""")
        ])

        settings = get_settings()
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        ).with_structured_output(TechnicalSkillSelection)

        try:
            result = (prompt | llm).invoke({})
            skills = [skill.strip() for skill in result.skills if skill.strip()]
            return skills[:num_skills]
        except Exception as exc:
            print(f"[SkillSelect] LLM selection failed: {exc}")
            return []

    def _select_skills_fallback(self, num_skills: int) -> List[str]:
        """
        평가할 기술 선정 (휴리스틱)

        우선순위:
        1. 구조화 면접에서 언급 + 프로필에 있는 기술
        2. 프로필에만 있는 기술
        3. 구조화 면접 technical_keywords, interests, emphasized_experiences
        4. 직무명(tagline) 기반
        5. 기본 역량 키워드
        """
        mentioned_skills = set(self.general_analysis.technical_keywords)

        # 프로필에서 기술 추출
        profile_skills = []

        # 경력 summary에서 추출
        for exp in self.profile.experiences:
            if exp.summary:
                profile_skills.extend([kw.strip() for kw in exp.summary.split(',') if kw.strip()])

        # 직무명(title)도 추가
        profile_skills.extend([exp.title for exp in self.profile.experiences])

        # 자격증도 추가
        profile_skills.extend([cert.name for cert in self.profile.certifications])

        # 중복 제거
        profile_skills = list(set(profile_skills))
        mentioned_list = list(mentioned_skills)

        # 1순위: 면접 언급 + 프로필 교집합 (가장 확실)
        intersection_skills = [s for s in mentioned_list if s in profile_skills]

        # 2순위: 면접에서만 언급 (면접 중요도 높음)
        mentioned_only = [s for s in mentioned_list if s not in profile_skills]

        # 3순위: 프로필에만 있음
        profile_only = [s for s in profile_skills if s not in mentioned_skills]

        # 합쳐서 선택
        selected = (intersection_skills + mentioned_only + profile_only)[:num_skills]

        # 부족하면 general_analysis에서 적극적으로 추출
        if len(selected) < num_skills:
            # technical_keywords에서 추가
            remaining = [s for s in mentioned_skills if s not in selected]
            selected.extend(remaining[:num_skills - len(selected)])

        # 여전히 부족하면 interests, emphasized_experiences 활용
        if len(selected) < num_skills:
            candidates = []
            candidates.extend(self.general_analysis.interests)
            candidates.extend(self.general_analysis.emphasized_experiences)
            for skill in candidates:
                if skill not in selected and len(selected) < num_skills:
                    selected.append(skill)

        # 여전히 부족하면 tagline 기반
        if len(selected) < num_skills and self.profile.basic and self.profile.basic.tagline:
            tagline = self.profile.basic.tagline
            if tagline not in selected:
                selected.append(tagline)

        # 최종 fallback: 기본 역량으로 무조건 채우기
        if len(selected) < num_skills:
            default_skills = [
                "직무 전반 역량",
                "프로젝트 수행 능력",
                "문제 해결 능력",
                "기술 역량",
                "협업 및 커뮤니케이션",
                "학습 및 성장 능력"
            ]
            for skill in default_skills:
                if len(selected) >= num_skills:
                    break
                if skill not in selected:
                    selected.append(skill)

        # 무조건 num_skills 개수 보장
        return selected[:num_skills]

    def get_next_question(self) -> Optional[dict]:
        """
        다음 질문 생성

        Returns:
            {
                "skill": str,
                "question_number": int,
                "question": str,
                "why": str,
                "progress": str
            }
        """
        if self.is_finished():
            return None

        skill = self.skills[self.current_skill_idx]

        # 현재 기술의 이전 답변들
        previous_answers = self.results[skill]

        # 전체 기술의 질문 이력 수집 (중복 검증용)
        all_questions = []
        for s in self.skills:
            for qa in self.results[s]:
                all_questions.append({
                    "skill": s,
                    "question": qa["question"],
                    "question_number": qa.get("question_number"),
                    "answer": qa.get("answer"),
                })

        # LLM으로 개인화된 질문 생성
        question_obj = generate_personalized_question(
            skill=skill,
            question_number=self.current_question_num,
            profile=self.profile,
            general_analysis=self.general_analysis,
            previous_skill_answers=previous_answers,
            all_previous_questions=all_questions,  # 추가
            use_langgraph_for_questions=self.use_langgraph_for_questions
        )

        self.current_question = {
            "skill": skill,
            "question_number": self.current_question_num,
            "question": question_obj.question,
            "why": question_obj.why
        }

        total_questions = len(self.skills) * self.questions_per_skill
        return {
            **self.current_question,
            "progress": f"{self.get_total_answered() + 1}/{total_questions}"
        }

    def submit_answer(self, answer: str) -> dict:
        """
        답변 제출 및 분석

        Args:
            answer: 답변 텍스트

        Returns:
            {
                "feedback": dict,
                "next_question": dict or None
            }
        """
        if not self.current_question:
            raise ValueError("질문을 먼저 받아야 합니다.")

        skill = self.current_question["skill"]
        question = self.current_question["question"]

        # LLM 분석 (점수 없음)
        feedback = analyze_answer(
            question=question,
            answer=answer,
            skill=skill
        )

        # 결과 저장
        self.results[skill].append({
            "question_number": self.current_question_num,
            "question": question,
            "answer": answer,
            "feedback": {
                "key_points": feedback.key_points,
                "mentioned_technologies": feedback.mentioned_technologies,
                "depth_areas": feedback.depth_areas,
                "follow_up_direction": feedback.follow_up_direction
            }
        })

        # 다음 상태로 이동
        self._move_next()

        return {
            "feedback": {
                "key_points": feedback.key_points,
                "depth_areas": feedback.depth_areas
            },
            "next_question": self.get_next_question()
        }

    def _move_next(self):
        """다음 질문으로 상태 이동"""
        self.current_question_num += 1

        # 한 기술의 질문 완료?
        if self.current_question_num > self.questions_per_skill:
            self.current_question_num = 1
            self.current_skill_idx += 1

        self.current_question = None

    def is_finished(self) -> bool:
        """모든 면접 완료 여부"""
        return self.current_skill_idx >= len(self.skills)

    def get_total_answered(self) -> int:
        """총 답변 개수"""
        return sum(len(answers) for answers in self.results.values())

    def get_results(self) -> dict:
        """최종 결과 반환 (점수 없음)"""
        return {
            "skills_evaluated": self.skills,
            "results": self.results,
            "total_questions": self.get_total_answered()
        }
