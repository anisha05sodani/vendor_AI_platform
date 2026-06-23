"""
Multi-Agent Orchestrator — LangGraph Pipeline
Chains all 4 agents in sequence with conditional routing.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Any
from agents.state import VendorState
from agents.document_verification_agent import document_verification_agent
from agents.qualification_agent import vendor_qualification_agent
from agents.fraud_agent import fraud_detection_agent
from agents.compliance_agent import compliance_agent
from agents.kpi_agent import kpi_agent


# LangGraph requires a plain TypedDict as state schema
class GraphState(TypedDict):
    vendor_name: str
    vendor_email: str
    business_type: str
    annual_revenue: float
    country: str
    documents_submitted: list
    documents: list
    document_verification_result: Optional[dict]
    qualification_result: Optional[dict]
    fraud_result: Optional[dict]
    compliance_result: Optional[dict]
    kpi_summary: Optional[dict]
    final_decision: Optional[str]
    pipeline_status: str
    error: Optional[str]


def _to_pydantic(state: GraphState) -> VendorState:
    return VendorState(**{k: state.get(k) for k in VendorState.model_fields})


def _to_graph(vendor: VendorState) -> GraphState:
    return vendor.model_dump()


def run_qualification(state: GraphState) -> GraphState:
    vendor = _to_pydantic(state)
    updated = vendor_qualification_agent(vendor)
    return _to_graph(updated)


def run_document_verification(state: GraphState) -> GraphState:
    vendor = _to_pydantic(state)
    updated = document_verification_agent(vendor)
    return _to_graph(updated)


def run_fraud(state: GraphState) -> GraphState:
    vendor = _to_pydantic(state)
    updated = fraud_detection_agent(vendor)
    return _to_graph(updated)


def run_compliance(state: GraphState) -> GraphState:
    vendor = _to_pydantic(state)
    updated = compliance_agent(vendor)
    return _to_graph(updated)


def run_kpi(state: GraphState) -> GraphState:
    vendor = _to_pydantic(state)
    updated = kpi_agent(vendor)
    return _to_graph(updated)


def should_continue_after_fraud(state: GraphState) -> str:
    """Skip compliance & KPI if fraud score is critically high."""
    fraud = state.get("fraud_result") or {}
    if fraud.get("fraud_score", 0) >= 85:
        state["final_decision"] = "REJECTED"
        state["pipeline_status"] = "completed"
        return "end"
    return "compliance"


def build_pipeline() -> StateGraph:
    graph = StateGraph(GraphState)

    graph.add_node("document_verification", run_document_verification)
    graph.add_node("qualification", run_qualification)
    graph.add_node("fraud", run_fraud)
    graph.add_node("compliance", run_compliance)
    graph.add_node("kpi", run_kpi)

    graph.set_entry_point("document_verification")
    graph.add_edge("document_verification", "qualification")
    graph.add_edge("qualification", "fraud")
    graph.add_conditional_edges(
        "fraud",
        should_continue_after_fraud,
        {"compliance": "compliance", "end": END},
    )
    graph.add_edge("compliance", "kpi")
    graph.add_edge("kpi", END)

    return graph.compile()


def run_pipeline(vendor_data: dict) -> dict:
    pipeline = build_pipeline()
    initial_state: GraphState = {
        "vendor_name": vendor_data["vendor_name"],
        "vendor_email": vendor_data["vendor_email"],
        "business_type": vendor_data["business_type"],
        "annual_revenue": vendor_data["annual_revenue"],
        "country": vendor_data["country"],
        "documents_submitted": vendor_data["documents_submitted"],
        "documents": vendor_data.get("documents", []),
        "document_verification_result": None,
        "qualification_result": None,
        "fraud_result": None,
        "compliance_result": None,
        "kpi_summary": None,
        "final_decision": None,
        "pipeline_status": "running",
        "error": None,
    }
    result = pipeline.invoke(initial_state)
    return result
