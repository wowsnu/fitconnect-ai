"""
LangGraph 기반 Situational 동적 질문 생성
기존 _generate_dynamic_questions 로직을 LangGraph로 전환
"""

from typing import List, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ai.interview.company.models import (
    CompanyGeneralAnalysis,
    TechnicalRequirements,
    RecommendedQuestions,
    CompanyInterviewQuestion
)
from config.settings import get_settings


def _escape_curly(text: str) -> str:
    if not text:
        return ""
    return text.replace("{", "{{").replace("}", "}}")


# ==================== State 정의 ====================

class SituationalQuestionState(TypedDict):
    """Situational 동적 질문 생성 State"""
    # Input - 기존 _generate_dynamic_questions에서 사용하던 모든 컨텍스트
    general_analysis: CompanyGeneralAnalysis
    technical_requirements: TechnicalRequirements
    fixed_answers: List[dict]  # [{"question": str, "answer": str, "type": str}]
    company_info: dict  # {culture, vision_mission}

    # Process
    generated_questions: List[CompanyInterviewQuestion]
    validation_errors: List[str]
    attempts: int
    llm_feedback: str

    # Output
    final_questions: List[CompanyInterviewQuestion]
    is_valid: bool


def _format_question_history(fixed_answers: List[dict], previous_generated: List[CompanyInterviewQuestion] = None, limit: int = 8) -> str:
    history_lines = []
    for ans in fixed_answers[-limit:]:
        question = (ans.get("question") or "").strip()
        if question:
            history_lines.append(f"- [고정] {question}")

    if previous_generated:
        for q in previous_generated[-limit:]:
            text = (q.question or "").strip()
            if text:
                history_lines.append(f"- [이전 동적] {text}")

    return "\n".join(history_lines) if history_lines else "없음"


def _format_question_history(fixed_answers: List[dict], previous_generated: List[CompanyInterviewQuestion] = None, limit: int = 8) -> str:
    """기존 질문 목록 요약"""
    history_lines = []
    for ans in fixed_answers[-limit:]:
        question = (ans.get("question") or "").strip()
        if question:
            history_lines.append(f"- [고정] {question}")

    if previous_generated:
        for q in previous_generated[-limit:]:
            text = (q.question or "").strip()
            if text:
                history_lines.append(f"- [이전 동적] {text}")

    return "\n".join(history_lines) if history_lines else "없음"


# ==================== Generator Node ====================

def generate_situational_questions_node(state: SituationalQuestionState) -> SituationalQuestionState:
    """
    Situational 질문 생성 노드

    기존 situational.py의 _generate_dynamic_questions 로직을 그대로 사용
    """
    print(f"[Generator] Generating Situational questions (attempt {state['attempts'] + 1})")

    general_analysis = state["general_analysis"]
    technical_requirements = state["technical_requirements"]
    fixed_answers = state["fixed_answers"]
    company_info = state["company_info"]
    question_history = _format_question_history(fixed_answers, state.get("generated_questions"))

    previous_failure_context = ""
    if state["attempts"] > 0 and state.get("validation_errors"):
        prev_questions = "\n".join(
            f"{idx+1}. {q.question}"
            for idx, q in enumerate(state.get("generated_questions") or [])
        ) or "이전 생성 없음"
        previous_failure_context = f"""
**⚠️ 이전 시도 실패 이유:**
{chr(10).join(f"- {err}" for err in state["validation_errors"])}

**이전에 생성한 질문들 (사용 불가):**
{prev_questions}

위 실패 이유를 참고하여, 중복되지 않는 새로운 질문 3개를 생성하세요.
"""

    # 1. 고정 질문 답변 포맷팅
    all_qa = "\n\n".join([
        f"질문: {a['question']}\n답변: {a['answer']}"
        for a in fixed_answers
    ])

    # 2. 이전 단계 분석 결과 요약
    context = f"""
[General 면접 분석 결과]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}

[Technical 면접 분석 결과]
- 직무: {technical_requirements.job_title}
- 필수 역량: {', '.join(technical_requirements.required_skills)}
- 예상 도전: {technical_requirements.expected_challenges}
"""

    # 3. 기업 정보 추가
    company_context = ""
    if company_info:
        company_parts = []
        if company_info.get("culture"):
            company_parts.append(f"- 조직 문화: {company_info['culture']}")
        if company_info.get("vision_mission"):
            company_parts.append(f"- 비전/미션: {company_info['vision_mission']}")

        if company_parts:
            company_context = "\n[기업 정보]\n" + "\n".join(company_parts) + "\n"

    # 4. 프롬프트 구성 (기존과 동일)
    context_safe = _escape_curly(context)
    company_context_safe = _escape_curly(company_context)
    all_qa_safe = _escape_curly(all_qa)
    question_history_safe = _escape_curly(question_history)
    previous_failure_safe = _escape_curly(previous_failure_context)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 인사팀 채용 담당자로, 공고(포지션)에 대한 정보를 자세히 파악하고자 실무진 부서와 인터뷰 중입니다.

질문과 답변 내용을 분석하여, Culture Fit(팀 핏)을 구체화할 수 있는 follow-up 질문을 정확히 3개 생성하세요.

**목표:**
- **해당 팀**을 위한 질문으로, 팀 문화 이해를 위해 실무진에게 던지는 질문
- 답변에서 언급된 팀 특성을 더 구체화
- 적합한 인재상을 명확히 정의
- General/Technical 결과와 일관성 확인

**질문 예시:**
- "팀에서 주도적으로 아이디어를 제안하고 실행하는 문화가 있나요?"
- "팀이 추구하는 가치나 행동 기준은 무엇이며, 후보자에게 요구되는 성향은 무엇인가요?"
- "팀은 수직적인 보고 구조인가요, 아니면 수평적인 협업 구조인가요?"

**중요:**
- 모든 질문을 한글로만 작성하세요 (영어 질문 금지)
- 실제 답변 내용을 바탕으로 질문 생성
- 팀 문화와 직무 특성을 연결하여 질문
- 정확히 3개의 질문만 생성
"""),
        ("user", f"""{context_safe}{company_context_safe}
[Situational 고정 질문 답변]
{all_qa_safe}

**이미 진행한 질문 목록(최대 8개):**
{question_history_safe}
{previous_failure_safe}

→ 위 질문들과 동일/유사한 내용을 반복하지 말고, 새로운 팀 문화/핏 질문 3개를 생성하세요.
""")
    ])

    # 5. LLM 호출
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(RecommendedQuestions)

    result = (prompt | llm).invoke({})

    # 6. State 업데이트
    state["generated_questions"] = result.questions
    state["attempts"] += 1

    print(f"[Generator] Generated {len(result.questions)} questions")

    return state


# ==================== Validator Node ====================

class CompanySituationalValidationResult(BaseModel):
    """LLM structured validation result for situational questions"""
    is_valid: bool = Field(..., description="True if all questions meet the guidelines")
    issues: List[str] = Field(default_factory=list)
    reasoning: str = Field(..., description="Evaluation reasoning")


def validate_situational_questions_llm_node(state: SituationalQuestionState) -> SituationalQuestionState:
    """LLM 기반 의미 검증"""
    print(f"[Validator:LLM] Evaluating {len(state['generated_questions'])} situational questions with LLM")

    generated_questions = state["generated_questions"]
    general_analysis = state["general_analysis"]
    technical_requirements = state["technical_requirements"]

    question_block = "\n\n".join([
        f"{idx+1}. 질문: {q.question}\n   목적: {getattr(q, 'purpose', '')}"
        for idx, q in enumerate(generated_questions)
    ]) or "생성된 질문 없음"

    context_summary = f"""
[General 분석]
- 핵심 가치: {', '.join(general_analysis.core_values)}
- 이상적 인재: {', '.join(general_analysis.ideal_candidate_traits)}
- 팀 문화: {general_analysis.team_culture}

[Technical 분석]
- 직무: {technical_requirements.job_title}
- 필수 역량: {', '.join(technical_requirements.required_skills)}
- 예상 도전: {technical_requirements.expected_challenges}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 인사팀 채용 담당자입니다. 아래 팀 문화/핏 질문들이 조건을 충족하는지 평가하세요.
조건:
1. 질문 수는 3개여야 하며, 각각 다른 팀 문화/협업/인재상 측면을 다뤄야 합니다.
2. General/Technical 분석 및 고정 답변을 근거로 구체적인 후속 질문이어야 합니다.
3. 질문은 한글이며, 실무 상황을 가정하고 지원자가 행동을 설명할 수 있어야 합니다.
4. 중복되거나 모호한 질문은 허용되지 않습니다.

모든 조건이 충족되지 않으면 is_valid=False로 두고 issues에 이유를 적으세요.
"""),
        ("user", f"""
{context_summary}

[생성된 질문들]
{question_block}
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(CompanySituationalValidationResult)

    result = (prompt | llm).invoke({})

    state["validation_errors"] = list(result.issues or [])
    state["llm_feedback"] = result.reasoning
    state["is_valid"] = result.is_valid and not state["validation_errors"]

    if result.is_valid:
        print("[Validator:LLM] ✅ Semantic validation passed")
    else:
        print(f"[Validator:LLM] ❌ Semantic validation failed: {state['validation_errors']}")

    return state


def validate_situational_questions_node(state: SituationalQuestionState) -> SituationalQuestionState:
    """기본 휴리스틱 검증"""
    print(f"[Validator:Heuristic] Running safety checks on {len(state['generated_questions'])} questions")

    errors = list(state.get("validation_errors", []))
    generated_questions = state["generated_questions"]

    if len(generated_questions) != 3:
        errors.append(f"Expected exactly 3 questions, got {len(generated_questions)}")

    seen = set()
    for idx, q in enumerate(generated_questions, 1):
        text = (q.question or "").strip()
        if len(text) < 15:
            errors.append(f"Question {idx} is too short.")
        if len(text) > 130:
            errors.append(f"Question {idx} is too long (maximum 130 characters).")
        english_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
        korean_chars = sum(1 for c in text if '가' <= c <= '힣')
        if korean_chars <= english_chars:
            errors.append(f"Question {idx} must be primarily in Korean.")

        seen.add(text)

    state["validation_errors"] = errors
    state["is_valid"] = state["is_valid"] and len(errors) == 0

    if state["is_valid"]:
        print("[Validator:Heuristic] ✅ Validation passed")
        state["final_questions"] = generated_questions
    else:
        print(f"[Validator:Heuristic] ❌ Validation failed: {errors}")

    return state


# ==================== Decision Logic ====================

def should_regenerate_situational(state: SituationalQuestionState) -> Literal["regenerate", "finish"]:
    """
    재생성 여부 결정

    - 검증 통과: finish
    - 검증 실패 + 최대 시도 횟수 미만: regenerate
    - 검증 실패 + 최대 시도 횟수 도달: finish (현재 질문 사용)
    """
    max_attempts = 5

    if state["is_valid"]:
        print("[Decision] Questions are valid. Finishing.")
        return "finish"

    if state["attempts"] >= max_attempts:
        print(f"[Decision] Max attempts ({max_attempts}) reached. Using current questions anyway.")
        # 최대 시도 횟수 도달 시 현재 질문으로 진행
        state["final_questions"] = state.get("generated_questions", [])
        return "finish"

    print(f"[Decision] Invalid. Regenerating... (attempt {state['attempts']}/{max_attempts})")
    return "regenerate"


# ==================== Graph 구축 ====================

def create_situational_question_graph() -> StateGraph:
    """
    Situational 동적 질문 생성 Graph

    Flow:
    START → generator → validator → [decision] → (regenerate → generator) or (finish → END)
    """
    workflow = StateGraph(SituationalQuestionState)

    # 노드 추가
    workflow.add_node("generator", generate_situational_questions_node)
    workflow.add_node("validator_llm", validate_situational_questions_llm_node)
    workflow.add_node("validator", validate_situational_questions_node)

    # Edge 추가
    workflow.set_entry_point("generator")
    workflow.add_edge("generator", "validator_llm")
    workflow.add_edge("validator_llm", "validator")

    # Conditional Edge: validator 후 재생성 또는 종료
    workflow.add_conditional_edges(
        "validator",
        should_regenerate_situational,
        {
            "regenerate": "generator",  # 재생성
            "finish": END  # 종료
        }
    )

    return workflow.compile()


# ==================== Public API ====================

def generate_situational_dynamic_questions(
    general_analysis: CompanyGeneralAnalysis,
    technical_requirements: TechnicalRequirements,
    fixed_answers: List[dict],
    company_info: dict = None
) -> List[CompanyInterviewQuestion]:
    """
    Situational 동적 질문 생성 (LangGraph 기반)

    기존 CompanySituationalInterview._generate_dynamic_questions()를
    대체하는 함수

    Args:
        general_analysis: General 면접 분석 결과
        technical_requirements: Technical 면접 분석 결과
        fixed_answers: 고정 질문 답변 리스트 [{"question": str, "answer": str, "type": "fixed"}]
        company_info: 기업 정보 dict (culture, vision_mission)

    Returns:
        생성된 질문 목록 (3개)
    """
    print(f"\n{'='*60}")
    print(f"Situational Dynamic Question Generation (LangGraph)")
    print(f"{'='*60}\n")

    # 초기 State
    initial_state: SituationalQuestionState = {
        "general_analysis": general_analysis,
        "technical_requirements": technical_requirements,
        "fixed_answers": fixed_answers,
        "company_info": company_info or {},
        "generated_questions": [],
        "validation_errors": [],
        "attempts": 0,
        "llm_feedback": "",
        "final_questions": [],
        "is_valid": False
    }

    # Graph 실행
    graph = create_situational_question_graph()
    final_state = graph.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"✅ Generation Complete!")
    print(f"Attempts: {final_state['attempts']}")
    print(f"Final Questions: {len(final_state.get('final_questions') or [])}")
    print(f"Valid: {final_state['is_valid']}")
    print(f"{'='*60}\n")

    return final_state["final_questions"]
