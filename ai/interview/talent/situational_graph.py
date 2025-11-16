"""
LangGraph 기반 Talent Situational 심화 질문 생성
기존 generate_deep_dive_question 로직을 LangGraph로 전환
"""

from typing import List, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config.settings import get_settings


# ==================== State 정의 ====================

class TalentSituationalQuestionState(TypedDict):
    """Talent Situational 심화 질문 생성 State"""
    # Input
    dominant_trait: str  # 가장 강한 성향
    dimension: str  # 해당 차원
    qa_history: List[dict]  # 이전 질문-답변 이력

    # Process
    generated_question: str
    validation_errors: List[str]
    attempts: int
    llm_feedback: str

    # Output
    final_question: str
    is_valid: bool


# ==================== Generator Node ====================

def generate_situational_deep_dive_question_node(state: TalentSituationalQuestionState) -> TalentSituationalQuestionState:
    """
    Situational 심화 질문 생성 노드

    기존 talent/situational.py의 generate_deep_dive_question 로직 사용
    """
    print(f"[Generator] Generating Situational deep-dive question (attempt {state['attempts'] + 1})")

    dominant_trait = state["dominant_trait"]
    dimension = state["dimension"]
    qa_history = state["qa_history"]

    # 이전 답변 요약
    history_text = "\n".join([
        f"Q: {qa['question']}\nA: {qa['answer'][:100]}..."
        for qa in qa_history[-3:]  # 최근 3개만
    ])

    dimension_map = {
        "work_style": "업무 스타일",
        "problem_solving": "문제 해결 방식",
        "learning": "학습 성향",
        "stress_response": "스트레스 대응",
        "communication": "커뮤니케이션"
    }

    # 이전 시도 실패 이유 (첫 시도가 아닐 때만)
    previous_failure_context = ""
    if state["attempts"] > 0 and state.get("validation_errors"):
        previous_failure_context = f"""
**⚠️ 이전 시도 실패 이유:**
{chr(10).join(f"- {err}" for err in state["validation_errors"])}

**피드백:**
{state.get("llm_feedback", "")}

**이전에 생성한 질문 (사용 불가):**
"{state.get("generated_question", "")}"

👉 위 실패 이유를 참고하여 **다른 각도**로 접근하세요. 같은 주제나 유사한 상황을 반복하지 마세요.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""당신은 인사팀 채용 담당자입니다.

        지원자의 [{dominant_trait}] 성향을 깊이 파악하기 위한 구체적인 심층 질문 1개를 생성하세요.

        이전 답변:
        {history_text}
        {previous_failure_context}

        **심화 질문 생성 가이드:**
        - {dimension_map.get(dimension, dimension)} 차원에서 [{dominant_trait}] 성향을 더 깊이 확인
        - **실제 경험했던 구체적인 상황을 물어보기** (가정 질문이 아니라 과거 경험 질문)
        - 이전 답변에서 애매했던 부분을 명확히 하되, 이전과 비슷한 내용을 묻지 않기
        - **경험에서 어떤 고민을 했고, 왜 그렇게 행동했는지 의사결정 배경을 드러내도록 질문**
        - 예/아니오로 답할 수 없는 열린 질문
        - 특정 직군에 국한되지 않는 범용적인 경험 질문
        - 인터뷰 대상자가 이해하기 쉽고 자연스러운 질문
        - 모든 질문을 한글로만 작성 (영어 질문 금지)
        - **질문 길이는 130자 이내로 간결하게 작성**

        **예시:**
        - 주도형 → "팀이나 리더의 결정이 조직 목표와 맞지 않다고 느낄 때 어떻게 행동하시나요? 구체적인 사례를 들어 말씀해주세요."
        - 분석형 → "새로운 프로젝트나 문제를 맡았을 때, 문제의 원인을 분석하고 해결책을 설계한 경험이 있나요? 과정과 결과를 중심으로 말씀해주세요."
        - 협력형 → "팀 내 의견이 갈렸을 때, 다양한 관점을 조율하여 합의를 도출한 경험이 있나요? 실제 행동과 결과 중심으로 설명해주세요."
"""),
        ("user", f"[{dominant_trait}] 성향을 깊이 파악할 수 있는 '구체적인' 상황 질문 1개를 생성하세요.")
    ])

    # LLM 호출
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.5,
        api_key=settings.OPENAI_API_KEY
    )

    result = (prompt | llm).invoke({})

    # State 업데이트
    state["generated_question"] = result.content
    state["attempts"] += 1

    print(f"[Generator] Generated question: {result.content[:50]}...")

    return state


# ==================== Validator Nodes ====================

class SituationalQuestionValidationResult(BaseModel):
    """LLM structured output for situational question validation"""
    is_valid: bool = Field(..., description="True if the question follows all guidelines")
    issues: List[str] = Field(default_factory=list, description="Detected issues or violations")
    reasoning: str = Field(..., description="Evaluation reasoning")


def validate_situational_question_llm_node(state: TalentSituationalQuestionState) -> TalentSituationalQuestionState:
    """LLM 기반 의미 검증"""
    print("[Validator:LLM] Evaluating situational question with LLM")

    generated_question = (state["generated_question"] or "").strip()
    dominant_trait = state["dominant_trait"]
    dimension = state["dimension"]
    qa_history = state.get("qa_history") or []

    dimension_map = {
        "work_style": "업무 스타일",
        "problem_solving": "문제 해결 방식",
        "learning": "학습 성향",
        "stress_response": "스트레스 대응",
        "communication": "커뮤니케이션"
    }
    dimension_keyword = dimension_map.get(dimension, dimension)

    # 이전 Q 요약
    prev_summary = "\n".join([
        f"{idx}. Q: {qa.get('question', '')[:120]}\n   A: {qa.get('answer', '')[:200]}"
        for idx, qa in enumerate(qa_history[-3:], 1)
    ]) or "없음"

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 상황 면접 전문가입니다. 다음 질문이 아래 조건을 충족하는지 평가하세요.

조건:
1. dominant_trait와 dimension을 명확히 겨냥해야 합니다.
2. 이전 질문과 의미적으로 중복되면 안 됩니다. 
3. 지원자의 실제 행동을 끌어낼 수 있는 구체적인 열린 질문이어야 합니다.
4. 질문이 충분히 자연스럽고 특정 직군에 국한되지 않는 범용적인 상황으로 매끄럽게 작성되어야 합니다.

모든 조건이 충족되지 않으면 is_valid=False로 두고 issues에 이유를 적으세요."""),
        ("user", f"""
[Dominant Trait] {dominant_trait}
[Dimension] {dimension_keyword}

[Generated Question]
{generated_question}

[Recent Q&A]
{prev_summary}
""")
    ])

    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(SituationalQuestionValidationResult)

    result = (prompt | llm).invoke({})

    state["validation_errors"] = list(result.issues or [])
    state["llm_feedback"] = result.reasoning
    state["is_valid"] = result.is_valid and not state["validation_errors"]

    if result.is_valid:
        print("[Validator:LLM] ✅ Semantic validation passed")
    else:
        print(f"[Validator:LLM] ❌ Semantic validation failed: {state['validation_errors']}")

    return state


def validate_situational_question_node(state: TalentSituationalQuestionState) -> TalentSituationalQuestionState:
    """기본 휴리스틱 검증"""
    print("[Validator:Heuristic] Running safety checks")

    errors = list(state.get("validation_errors", []))
    generated_question = (state["generated_question"] or "").strip()

    # 길이 및 한글 비중
    if len(generated_question) < 20:
        errors.append("Question is too short (minimum 20 characters).")
    if len(generated_question) > 130:
        errors.append("Question is too long (maximum 130 characters).")

    english_chars = sum(1 for c in generated_question if 'a' <= c.lower() <= 'z')
    korean_chars = sum(1 for c in generated_question if '가' <= c <= '힣')
    if korean_chars <= english_chars:
        errors.append("Question must be primarily written in Korean.")


    state["validation_errors"] = errors
    state["is_valid"] = state["is_valid"] and len(errors) == 0

    if state["is_valid"]:
        print("[Validator:Heuristic] ✅ Validation passed")
        state["final_question"] = generated_question
    else:
        print(f"[Validator:Heuristic] ❌ Validation failed: {errors}")

    return state


# ==================== Decision Logic ====================

def should_regenerate_situational(state: TalentSituationalQuestionState) -> Literal["regenerate", "finish"]:
    """
    재생성 여부 결정

    - 검증 통과: finish
    - 검증 실패 + 최대 시도 횟수 미만: regenerate
    - 검증 실패 + 최대 시도 횟수 도달: finish (현재 질문 사용)
    """
    max_attempts = 5

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

def create_situational_deep_dive_question_graph() -> StateGraph:
    """
    Situational 심화 질문 생성 Graph

    Flow:
    START → generator → validator → [decision] → (regenerate → generator) or (finish → END)
    """
    workflow = StateGraph(TalentSituationalQuestionState)

    # 노드 추가
    workflow.add_node("generator", generate_situational_deep_dive_question_node)
    workflow.add_node("validator_llm", validate_situational_question_llm_node)
    workflow.add_node("validator", validate_situational_question_node)

    # Edge 추가
    workflow.set_entry_point("generator")
    workflow.add_edge("generator", "validator_llm")
    workflow.add_edge("validator_llm", "validator")

    # Conditional Edge: validator 후 재생성 또는 종료
    workflow.add_conditional_edges(
        "validator",
        should_regenerate_situational,
        {
            "regenerate": "generator",
            "finish": END
        }
    )

    return workflow.compile()


# ==================== Public API ====================

def generate_deep_dive_question_with_graph(
    dominant_trait: str,
    dimension: str,
    qa_history: List[dict]
) -> str:
    """
    Situational 심화 질문 생성 (LangGraph 기반)

    기존 talent/situational.py의 generate_deep_dive_question()를 대체하는 함수

    Args:
        dominant_trait: 가장 강한 성향 (예: "주도형", "분석형")
        dimension: 해당 차원 (예: "work_style", "problem_solving")
        qa_history: 이전 질문-답변 이력

    Returns:
        생성된 심화 질문 (str)
    """
    print(f"\n{'='*60}")
    print(f"Situational Deep-Dive Question Generation (LangGraph)")
    print(f"Trait: {dominant_trait}, Dimension: {dimension}")
    print(f"{'='*60}\n")

    # 초기 State
    initial_state: TalentSituationalQuestionState = {
        "dominant_trait": dominant_trait,
        "dimension": dimension,
        "qa_history": qa_history,
        "generated_question": "",
        "validation_errors": [],
        "attempts": 0,
        "llm_feedback": "",
        "final_question": "",
        "is_valid": False
    }

    # Graph 실행
    graph = create_situational_deep_dive_question_graph()
    final_state = graph.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"✅ Generation Complete!")
    print(f"Attempts: {final_state['attempts']}")
    print(f"Valid: {final_state['is_valid']}")
    print(f"Question: {final_state['final_question'][:80]}...")
    print(f"{'='*60}\n")

    return final_state["final_question"]
