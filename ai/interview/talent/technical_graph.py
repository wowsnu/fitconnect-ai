"""
LangGraph 기반 Talent Technical 동적 질문 생성
기존 generate_personalized_question 로직을 LangGraph로 전환
"""

from typing import List, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ai.interview.talent.models import (
    CandidateProfile,
    GeneralInterviewAnalysis,
    InterviewQuestion,
)
from config.settings import get_settings


# ==================== State 정의 ====================

class TalentTechnicalQuestionState(TypedDict):
    """Talent Technical 동적 질문 생성 State"""
    # Input
    skill: str  # 평가할 기술
    question_number: int  # 1, 2, 3
    profile: CandidateProfile
    general_analysis: GeneralInterviewAnalysis
    previous_skill_answers: List[dict]  # 현재 기술의 이전 답변들

    # Process
    generated_question: InterviewQuestion
    validation_errors: List[str]
    attempts: int
    llm_feedback: str

    # Output
    final_question: InterviewQuestion
    is_valid: bool


# ==================== Generator Node ====================

def generate_talent_technical_question_node(state: TalentTechnicalQuestionState) -> TalentTechnicalQuestionState:
    """
    Talent Technical 질문 생성 노드

    기존 talent/technical.py의 generate_personalized_question 로직 사용
    """
    print(f"[Generator] Generating Talent Technical question (attempt {state['attempts'] + 1})")

    skill = state["skill"]
    question_number = state["question_number"]
    profile = state["profile"]
    general_analysis = state["general_analysis"]
    previous_skill_answers = state["previous_skill_answers"] or []

    # 이전 답변 정리
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

    # 질문 번호에 따른 가이드
    if question_number == 1:
        depth_guide = """**1번째 질문 (도입):**
- 구조화 면접에서 언급한 핵심 주제나 관심사를 자연스럽게 연결
- 예1: "아까 데이터 기반 의사결정에 관심이 많다고 하셨는데, 실제로 어떤 경험이 있었나요?"
- 예2: "디자인 프로젝트에서 사용자 피드백을 반영했다고 하셨는데, 구체적으로 어떤 과정을 거치셨나요?"
- 지원자의 전반적인 역할, 경험에 대한 동기와 과정 탐색
"""
    elif question_number == 2:
        depth_guide = """**2번째 질문 (심화):**
- 1번째 답변에서 언급한 경험에 대해 구체적인 사례나 방법을 더 깊이 탐구
- 예1: 1번에서 "마케팅 캠페인 성과 분석"을 언급했다면 → "성과 측정 시 어떤 지표나 도구를 활용하셨나요?"
- 예2: 1번에서 "Redis 캐싱"을 언급했다면 → "Redis 캐싱 전략을 구체적으로 어떻게 설계하셨나요?"
- 실무 적용 과정, 문제 해결 접근법, 의사결정 근거 파악
"""
    else:  # question_number == 3
        depth_guide = """**3번째 질문 (심층 확장):**
- 앞선 답변(1, 2번)을 바탕으로 사고의 깊이, 확장성, 전이 능력을 탐색
- 단순한 사례 회고가 아니라, '그 경험을 통해 무엇을 배웠고 이후 어떻게 적용했는가'를 끌어내는 단계
- 예1: "그 경험을 통해 얻은 교훈이나 인사이트를 이후 다른 프로젝트에 어떻게 적용하셨나요?"
- 예2: "만약 같은 상황이 다시 온다면, 어떤 부분을 다르게 접근하고 싶으신가요?"
- 예3: "그 접근법을 선택한 이유가 있나요? 다른 아키텍처는 고려하지 않으셨나요?"
- 목표: 지원자의 사고 수준, 성장 가능성, 문제 재구조화 능력 파악
"""

    # 프로필에서 정보 추출
    job_category = profile.basic.tagline if profile.basic else ""

    # 경력 정보에서 기술 스택 추출
    skills: List[str] = []
    for exp in profile.experiences:
        if exp.summary:
            skills.extend([kw.strip() for kw in exp.summary.split(',') if kw.strip()])

    # 중복 제거 및 길이 제한
    unique_skills = sorted({s for s in skills if s})
    skills = unique_skills[:10]

    # 총 경력 계산
    total_experience = sum((exp.duration_years or 0) for exp in profile.experiences)

    # 경력사항 요약
    experience_entries = []
    for exp in profile.experiences:
        duration_text = f"{exp.duration_years}년" if exp.duration_years is not None else "기간 정보 없음"
        experience_entries.append(f"- {exp.company_name} / {exp.title} ({duration_text})")
    experience_summary = "\n".join(experience_entries)

    # 활동 요약
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

        **질문 원칙:**
        - 열린 질문 (지원자가 실제 경험을 말할 수 있도록 유도, 실무 중심의 구체적인 질문)
        - 사실 기반 질문 (프로필과 인터뷰 답변에 있는 내용만 사용하여 적절한 질문 생성, 제시되지 않은 경험을 만들어서 물어보지 말 것)
        - 추정 및 과장 금지 (언급되지 않은 내용을 만들어내지 말 것)
        - 유사 질문 금지 (의미없이 비슷한 질문을 하는 것은 지양)
        - 추가 질문일 경우 이전 답변에서 언급된 내용을 바탕으로 더 구체적이고 깊이 있는 후속 질문을 생성
        - 모든 질문을 한글로만 작성 (영어 질문 금지)
        - **질문 길이는 130자 이내로 간결하게 작성** (핵심만 담아 명확하게 전달)

        **예시:**
        - 새로운 교육 프로그램을 설계할 때, 학습자 요구나 조직의 목표를 어떻게 반영하셨나요? 설계 과정에서 어떤 의사결정을 내렸는지 구체적으로 말씀해 주세요.
        - 이전 답변에서 React 프로젝트를 진행하며 Redux를 사용했다고 답하셨는데, Redux를 선택한 이유는 무엇인가요? 그 선택이 프로젝트 구조나 성능에 어떤 영향을 주었는지도 설명해 주세요.
        """),
        ("user", f"""
현재 평가 기술: {skill}
질문 번호: {question_number}/3
{prev_context}

{skill}에 대한 {question_number}번째 질문을 생성하세요.
""")
    ])

    # LLM 호출
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(InterviewQuestion)

    result = (prompt | llm).invoke({})

    # State 업데이트
    state["generated_question"] = result
    state["attempts"] += 1

    print(f"[Generator] Generated question: {result.question[:50]}...")

    return state


# ==================== Validator Nodes ====================

class TechnicalQuestionValidationResult(BaseModel):
    """LLM structured output for question validation"""
    is_valid: bool = Field(..., description="True if the question follows all guidelines")
    issues: List[str] = Field(default_factory=list, description="Detected issues or violations")
    reasoning: str = Field(..., description="Brief reasoning of the evaluation")


def validate_talent_technical_question_llm_node(state: TalentTechnicalQuestionState) -> TalentTechnicalQuestionState:
    """LLM 기반 의미 검증"""
    print("[Validator:LLM] Evaluating question semantics with LLM")

    generated_question = state["generated_question"]
    question_text = (generated_question.question or "").strip()
    why_text = (generated_question.why or "").strip()
    skill = state["skill"]
    question_number = state["question_number"]
    previous_skill_answers = state.get("previous_skill_answers") or []

    # 이전 질문 요약
    prev_summary = ""
    if previous_skill_answers:
        prev_lines = []
        for idx, qa in enumerate(previous_skill_answers[-3:], 1):
            q = qa.get("question", "")[:120]
            a = qa.get("answer", "")[:200]
            prev_lines.append(f"{idx}. Q: {q}\n   A: {a}")
        prev_summary = "\n".join(prev_lines)
    else:
        prev_summary = "없음"

    stage_intent = {
        1: "지원자의 배경/동기/대표 경험을 파악하는 도입 질문",
        2: "이전 답변을 토대로 구체적인 방법과 판단 근거를 파고드는 심화 질문",
        3: "배운 점, 전이 가능성, 다른 접근을 묻는 확장 질문"
    }.get(question_number, "일반적인 후속 질문")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 시니어 인터뷰어입니다. 아래 질문이 가이드라인을 충족하는지 평가하세요.

검증 기준:
1. 질문이 지정된 기술(skill)을 명확히 언급하거나 해당 역량을 겨냥하는가?
2. question_number에 맞는 인터뷰 의도를 충족하는가? (도입/심화/확장)
3. 이전 질문과 중복되지 않고, 이전 답변을 자연스럽게 이어가는가?
4. 질문이 충분히 구체적이며 지원자가 실제 경험을 설명할 수 있도록 구성되어 있는가?
5. 'why' 설명이 질문 목적을 명확히 설명하는가?

is_valid가 False라면 issues에 이유를 구체적으로 나열하세요.""" ),
        ("user", f"""
[Skill] {skill}
[Question Number] {question_number}
[Stage Intent] {stage_intent}

[Question]
{question_text}

[Why]
{why_text}

[Previous Q&A]
{prev_summary}
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(TechnicalQuestionValidationResult)

    result = (prompt | llm).invoke({})

    state["validation_errors"] = list(result.issues or [])
    state["llm_feedback"] = result.reasoning
    state["is_valid"] = result.is_valid and not state["validation_errors"]

    if result.is_valid:
        print("[Validator:LLM] ✅ Semantic validation passed")
    else:
        print(f"[Validator:LLM] ❌ Semantic validation failed: {state['validation_errors']}")

    return state


def validate_talent_technical_question_node(state: TalentTechnicalQuestionState) -> TalentTechnicalQuestionState:
    """
    최소 휴리스틱 검증 (한글/길이/문장부호 등)
    """
    print("[Validator:Heuristic] Running basic safety checks")

    errors = list(state.get("validation_errors", []))
    generated_question = state["generated_question"]
    question_text = (generated_question.question or "").strip()
    why_text = (generated_question.why or "").strip()

    # 최소/최대 길이
    if len(question_text) < 20:
        errors.append("Question is too short (minimum 20 characters).")
    if len(question_text) > 130:
        errors.append("Question is too long (maximum 130 characters).")

    # 한글 비중 검사
    english_chars = sum(1 for c in question_text if 'a' <= c.lower() <= 'z')
    korean_chars = sum(1 for c in question_text if '가' <= c <= '힣')
    if korean_chars <= english_chars:
        errors.append("Question must be primarily written in Korean.")

    # why 필드 기본 길이
    if len(why_text) < 10:
        errors.append("Why explanation is too short (minimum 10 characters).")

    state["validation_errors"] = errors
    state["is_valid"] = state["is_valid"] and len(errors) == 0

    if state["is_valid"]:
        print("[Validator:Heuristic] ✅ Validation passed")
        state["final_question"] = generated_question
    else:
        print(f"[Validator:Heuristic] ❌ Validation failed: {errors}")

    return state


# ==================== Decision Logic ====================

def should_regenerate_talent_technical(state: TalentTechnicalQuestionState) -> Literal["regenerate", "finish"]:
    """
    재생성 여부 결정

    - 검증 통과: finish
    - 검증 실패 + 최대 시도 횟수 미만: regenerate
    - 검증 실패 + 최대 시도 횟수 도달: finish (현재 질문 사용)
    """
    max_attempts = 3

    if state["is_valid"]:
        print("[Decision] Question is valid. Finishing.")
        return "finish"

    if state["attempts"] >= max_attempts:
        print(f"[Decision] Max attempts ({max_attempts}) reached. Using current question anyway.")
        # 최대 시도 횟수 도달 시 현재 질문으로 진행
        state["final_question"] = state["generated_question"]
        return "finish"

    print(f"[Decision] Invalid. Regenerating... (attempt {state['attempts']}/{max_attempts})")
    return "regenerate"


# ==================== Graph 구축 ====================

def create_talent_technical_question_graph() -> StateGraph:
    """
    Talent Technical 동적 질문 생성 Graph

    Flow:
    START → generator → validator → [decision] → (regenerate → generator) or (finish → END)
    """
    workflow = StateGraph(TalentTechnicalQuestionState)

    # 노드 추가
    workflow.add_node("generator", generate_talent_technical_question_node)
    workflow.add_node("validator_llm", validate_talent_technical_question_llm_node)
    workflow.add_node("validator", validate_talent_technical_question_node)

    # Edge 추가
    workflow.set_entry_point("generator")
    workflow.add_edge("generator", "validator_llm")
    workflow.add_edge("validator_llm", "validator")

    # Conditional Edge: validator 후 재생성 또는 종료
    workflow.add_conditional_edges(
        "validator",
        should_regenerate_talent_technical,
        {
            "regenerate": "generator",
            "finish": END
        }
    )

    return workflow.compile()


# ==================== Public API ====================

def generate_personalized_question_with_graph(
    skill: str,
    question_number: int,
    profile: CandidateProfile,
    general_analysis: GeneralInterviewAnalysis,
    previous_skill_answers: List[dict] = None
) -> InterviewQuestion:
    """
    Talent Technical 개인화된 질문 생성 (LangGraph 기반)

    기존 talent/technical.py의 generate_personalized_question()를 대체하는 함수

    Args:
        skill: 평가할 기술
        question_number: 해당 기술의 몇 번째 질문인지 (1, 2, 3)
        profile: 지원자 프로필
        general_analysis: 구조화 면접 분석 결과
        previous_skill_answers: 현재 기술의 이전 답변들

    Returns:
        생성된 질문 (InterviewQuestion)
    """
    print(f"\n{'='*60}")
    print(f"Talent Technical Question Generation (LangGraph)")
    print(f"Skill: {skill}, Question #{question_number}")
    print(f"{'='*60}\n")

    # 초기 State
    initial_state: TalentTechnicalQuestionState = {
        "skill": skill,
        "question_number": question_number,
        "profile": profile,
        "general_analysis": general_analysis,
        "previous_skill_answers": previous_skill_answers or [],
        "generated_question": None,
        "validation_errors": [],
        "attempts": 0,
         "llm_feedback": "",
        "final_question": None,
        "is_valid": False
    }

    # Graph 실행
    graph = create_talent_technical_question_graph()
    final_state = graph.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"✅ Generation Complete!")
    print(f"Attempts: {final_state['attempts']}")
    print(f"Valid: {final_state['is_valid']}")
    print(f"Question: {final_state['final_question'].question[:80]}...")
    print(f"{'='*60}\n")

    return final_state["final_question"]
