"""
XAI Pipeline with LangChain + LangGraph (Summary-Based)

Simplified pipeline using only summaries and similarity scores.
No RAG, no vectorstore retrieval.

Graph Flow:
1. generate_stage1_field_result (6 fields)
2. aggregate_stage2_category (3 categories in parallel)
3. merge_all_categories
"""

from typing import List, Dict, Any, TypedDict, Literal, Annotated
from operator import add
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ai.matching.xai_models import Stage1FieldResult, Stage2CategoryResult
from config.settings import get_settings


# ==================== Pydantic Models (No Citations) ====================

class Stage1FieldResultSimple(BaseModel):
    """Stage 1 field result (summary-based, no citations)"""
    
    field: Literal["roles", "skills", "growth", "career", "vision", "culture"]
    matching_reason: str
    risk_or_gap: str
    suggested_questions: List[str]


class Stage2CategoryResultSimple(BaseModel):
    """Stage 2 category result (summary-based, no citations)"""
    
    category: Literal["직무 적합성", "성장 가능성", "문화 적합성"]
    matching_evidence: str
    check_points: str
    suggested_questions: List[str]


# ==================== LangGraph State ====================

class XAIGraphState(TypedDict):
    """State for XAI generation graph (summary-based only)"""
    
    # Input (overwrite only, 단일 dict)
    talent_summaries: Dict[str, str]  # {field: summary} (overwrite only)
    job_summaries: Dict[str, str]  # {field: summary} (overwrite only)
    similarity_scores: Dict[str, float]  # {field: score} (overwrite only)

    # Stage 1 results (add 누적)
    stage1_results: Annotated[List[Stage1FieldResultSimple], add]

    # Stage 2 results (overwrite only)
    job_fit_result: Stage2CategoryResultSimple
    growth_potential_result: Stage2CategoryResultSimple
    culture_fit_result: Stage2CategoryResultSimple

    # Final output (overwrite only)
    final_explanation: Dict[str, Any]


# ==================== LangGraph Nodes ====================


def generate_stage1_field_result_node(state: XAIGraphState) -> XAIGraphState:
    """Node 1: Generate Stage 1 field-level XAI for all 6 fields (summary-based only)"""
    
    print("[Node] Generating Stage 1 field results...")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(Stage1FieldResultSimple)
    
    stage1_results = []
    
    # Process all 6 fields
    for field in ["roles", "skills", "growth", "career", "vision", "culture"]:
        talent_summary = state["talent_summaries"].get(field, "")
        job_summary = state["job_summaries"].get(field, "")
        similarity = state["similarity_scores"].get(field, 0.0)
        
        # Build prompt (no RAG, no citations)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 인재-채용 매칭을 설명하는 HR 분석가입니다. 모든 출력은 한국어로 작성하세요.

**출력 필드**
1) matching_reason: 해당 분야에서 왜 매치가 되는지 근거 중심으로 설명 (200-300자)
2) risk_or_gap: 잠재 리스크/갭 또는 주의 사항 (200-300자)
3) suggested_questions: 면접 시 검증용 질문 2-3개 (각각 한 줄)

**가이드라인**
- 제공된 요약과 유사도 점수만 사용해 근거 기반으로 작성
- 재능/채용 요약을 비교해 정합성과 차이를 명확히 언급
- 질문은 구체적이고 실행 가능하게 작성
- 모든 문장과 질문은 자연스러운 한국어로 작성
"""),
            ("user", """
필드: {field}
유사도 점수: {similarity:.3f}

인재 요약:
{talent_summary}

채용 요약:
{job_summary}

위 정보를 기반으로 구조화된 출력을 완성하세요. 모든 응답은 한국어로 작성합니다.
""")
        ])
        
        # Generate result
        chain = prompt | llm
        result = chain.invoke({
            "field": field,
            "similarity": similarity,
            "talent_summary": talent_summary,
            "job_summary": job_summary
        })
        
        stage1_results.append(result)
        print(f"  ✓ Generated {field}")
    
    # Return only the updated key to avoid concurrent writes on other channels
    return {"stage1_results": stage1_results}


def aggregate_job_fit_node(state: XAIGraphState) -> XAIGraphState:
    """Node 4a: Aggregate 직무 적합성 (roles + skills)"""
    
    print("[Node] Aggregating 직무 적합성...")
    
    field_results = [
        r for r in state["stage1_results"]
        if r.field in ["roles", "skills"]
    ]
    
    result = _aggregate_category(
        category="직무 적합성",
        field_results=field_results
    )
    
    return {"job_fit_result": result}


def aggregate_growth_potential_node(state: XAIGraphState) -> XAIGraphState:
    """Node 4b: Aggregate 성장 가능성 (growth + career + vision)"""
    
    print("[Node] Aggregating 성장 가능성...")
    
    field_results = [
        r for r in state["stage1_results"]
        if r.field in ["growth", "career", "vision"]
    ]
    
    result = _aggregate_category(
        category="성장 가능성",
        field_results=field_results
    )
    
    return {"growth_potential_result": result}


def aggregate_culture_fit_node(state: XAIGraphState) -> XAIGraphState:
    """Node 4c: Aggregate 문화 적합성 (culture)"""
    
    print("[Node] Aggregating 문화 적합성...")
    
    field_results = [
        r for r in state["stage1_results"]
        if r.field == "culture"
    ]
    
    result = _aggregate_category(
        category="문화 적합성",
        field_results=field_results
    )
    
    return {"culture_fit_result": result}


def merge_all_categories_node(state: XAIGraphState) -> XAIGraphState:
    """Node 5: Merge all category results into final output"""
    
    print("[Node] Merging all categories...")
    
    final_explanation = {
        "직무 적합성": state["job_fit_result"].model_dump(),
        "성장 가능성": state["growth_potential_result"].model_dump(),
        "문화 적합성": state["culture_fit_result"].model_dump(),
        "metadata": {
            "total_stage1_fields": len(state["stage1_results"]),
            "total_categories": 3
        }
    }
    
    return {"final_explanation": final_explanation}


# ==================== Helper: Stage 2 Aggregation ====================

def _aggregate_category(
    category: str,
    field_results: List[Stage1FieldResultSimple]
) -> Stage2CategoryResultSimple:
    """Aggregate Stage 1 field results into Stage 2 category result (summary-based only)"""
    
    settings = get_settings()
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY
    ).with_structured_output(Stage2CategoryResultSimple)
    
    # Combine field contexts
    field_context = "\n\n".join([
        f"**Field: {fr.field}**\n"
        f"Matching Reason: {fr.matching_reason}\n"
        f"Risk/Gap: {fr.risk_or_gap}\n"
        f"Questions: {', '.join(fr.suggested_questions)}"
        for fr in field_results
    ])
    
    # Build prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 임원용 매칭 설명을 작성하는 HR 분석가입니다. 모든 출력은 한국어로 작성하세요.

**출력 필드**
1) matching_evidence: 해당 카테고리의 핵심 근거를 스토리처럼 연결 (300-400자)
2) check_points: 이 카테고리에서 반드시 검증해야 할 포인트
3) suggested_questions: 필드별 질문 중 가장 가치 있는 질문 3-5개

**가이드라인**
- 단순 요약이 아니라 근거를 엮어 설득력 있게 작성
- 실행 가능한 인사이트를 우선시
- 질문은 중복 없이 다각도로 선택
- 모든 문장은 자연스러운 한국어로 작성
"""),
        ("user", """
카테고리: {category}

필드별 분석 결과:
{field_context}

위 결과를 종합해 카테고리 수준 설명을 작성하세요. 모든 응답은 한국어로 작성합니다.
""")
    ])
    
    # Generate result
    chain = prompt | llm
    result = chain.invoke({
        "category": category,
        "field_context": field_context
    })
    
    print(f"  ✓ Aggregated {category}: {len(result.suggested_questions)} questions")
    
    return result


# ==================== LangGraph Construction ====================

def create_xai_graph() -> StateGraph:
    """Create XAI generation graph (simplified, no RAG)"""
    
    workflow = StateGraph(XAIGraphState)
    
    # Add nodes
    workflow.add_node("generate_stage1_results", generate_stage1_field_result_node)
    workflow.add_node("aggregate_job_fit", aggregate_job_fit_node)
    workflow.add_node("aggregate_growth_potential", aggregate_growth_potential_node)
    workflow.add_node("aggregate_culture_fit", aggregate_culture_fit_node)
    workflow.add_node("merge_all_categories", merge_all_categories_node)
    
    # Define edges (simplified flow)
    workflow.set_entry_point("generate_stage1_results")
    workflow.add_edge("generate_stage1_results", "aggregate_job_fit")
    workflow.add_edge("generate_stage1_results", "aggregate_growth_potential")
    workflow.add_edge("generate_stage1_results", "aggregate_culture_fit")
    
    # Wait for all aggregations to complete before merging
    workflow.add_edge("aggregate_job_fit", "merge_all_categories")
    workflow.add_edge("aggregate_growth_potential", "merge_all_categories")
    workflow.add_edge("aggregate_culture_fit", "merge_all_categories")
    
    workflow.add_edge("merge_all_categories", END)
    
    return workflow.compile()


# ==================== Public API ====================

def generate_match_explanation(
    talent_summaries: Dict[str, str],
    job_summaries: Dict[str, str],
    similarity_scores: Dict[str, float]
) -> Dict[str, Any]:
    """
    Generate complete match explanation using LangGraph (summary-based only)
    
    Args:
        talent_summaries: {field: summary} for 6 fields
        job_summaries: {field: summary} for 6 fields
        similarity_scores: {field: score} for 6 fields
    
    Returns:
        Final explanation with 3 categories:
        - 직무 적합성
        - 성장 가능성
        - 문화 적합성
    """
    print(f"\n{'='*60}")
    print(f"XAI Match Explanation Generation (Summary-Based)")
    print(f"{'='*60}\n")
    
    # Initialize state
    initial_state: XAIGraphState = {
        "talent_summaries": talent_summaries,
        "job_summaries": job_summaries,
        "similarity_scores": similarity_scores,
        "stage1_results": [],
        "job_fit_result": None,
        "growth_potential_result": None,
        "culture_fit_result": None,
        "final_explanation": {}
    }
    
    # Run graph
    graph = create_xai_graph()
    final_state = graph.invoke(initial_state)
    
    print(f"\n{'='*60}")
    print(f"✅ XAI Generation Complete!")
    print(f"Stage 1 Fields: {len(final_state['stage1_results'])}")
    print(f"Stage 2 Categories: 3")
    print(f"{'='*60}\n")
    
    return final_state["final_explanation"]
