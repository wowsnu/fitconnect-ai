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
    
    # Input
    talent_summaries: Dict[str, str]  # {field: summary}
    job_summaries: Dict[str, str]  # {field: summary}
    similarity_scores: Dict[str, float]  # {field: score}
    
    # Stage 1 results (accumulated)
    stage1_results: Annotated[List[Stage1FieldResultSimple], add]
    
    # Stage 2 results
    job_fit_result: Stage2CategoryResultSimple
    growth_potential_result: Stage2CategoryResultSimple
    culture_fit_result: Stage2CategoryResultSimple
    
    # Final output
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
            ("system", """You are an expert HR analyst specializing in talent-job matching with explainable AI.

Analyze the given field and provide a comprehensive explanation based on the summaries and similarity score.

**Your Task:**
1. **matching_reason**: Explain why the talent and job match in this field based on the summaries
2. **risk_or_gap**: Identify potential risks, gaps, or areas of concern
3. **suggested_questions**: Provide 2-3 validation questions for interviewers

**Guidelines:**
- Be specific and evidence-based using only the provided summaries
- Compare talent and job summaries to identify alignment and gaps
- Suggest actionable, insightful questions
- Keep explanations concise but thorough (200-300 chars each)
"""),
            ("user", """
Field: {field}
Similarity Score: {similarity:.3f}

Talent Summary:
{talent_summary}

Job Summary:
{job_summary}

Analyze this field and provide structured output.
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
    
    state["stage1_results"] = stage1_results
    return state


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
    
    state["job_fit_result"] = result
    return state


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
    
    state["growth_potential_result"] = result
    return state


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
    
    state["culture_fit_result"] = result
    return state


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
    
    state["final_explanation"] = final_explanation
    return state


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
        ("system", """You are an expert HR analyst creating executive-level match explanations.

Your task is to aggregate multiple field-level analyses into a single, coherent category-level explanation.

**Your Output:**
1. **matching_evidence**: Synthesize evidence from all fields into a compelling narrative
2. **check_points**: Highlight critical validation points for this category
3. **suggested_questions**: Curate 3-5 best questions from field-level suggestions

**Guidelines:**
- Create a cohesive story, not just a summary
- Prioritize actionable insights
- Keep evidence clear and concise (300-400 chars)
- Select diverse, high-value questions
"""),
        ("user", """
Category: {category}

Field-level Analysis Results:
{field_context}

Aggregate these field results into a category-level explanation.
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
