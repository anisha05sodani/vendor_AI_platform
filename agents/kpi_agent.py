"""
Agent 4 — Executive KPI Summary Agent
Produces a business-level summary for leadership dashboards.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from .state import VendorState
import json


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)


def kpi_agent(state: VendorState) -> VendorState:
    qual = state.qualification_result or {}
    fraud = state.fraud_result or {}
    comp = state.compliance_result or {}
    docs = state.document_verification_result or {}

    prompt = f"""
You are an executive assistant. Produce a KPI summary as JSON with:
- overall_score (0-100)
- decision ("APPROVED" | "PENDING_REVIEW" | "REJECTED")
- key_metrics (dict with: risk_level, fraud_score, compliance_status, missing_docs_count, document_status)
- executive_summary (3-4 sentence string for leadership)
- next_steps (list of action strings)

DECISION RULES (follow strictly):
- APPROVED: eligible=true AND risk_level="low" AND fraud_score<40 AND (compliance_status="compliant" OR compliance_status="partially_compliant") AND missing_docs_count<=1 AND document_status="complete"
- REJECTED: fraud_score>=85 OR eligible=false OR compliance_status="non_compliant"
- PENDING_REVIEW: all other cases

DOCUMENT RULES (apply on top of the above):
- If any REQUIRED document is missing or invalid, the vendor must NOT be APPROVED.
  Downgrade to at least PENDING_REVIEW (or REJECTED if a critical required
  document such as business registration or tax ID is missing/invalid).
- Any document concern (missing/invalid/unreadable required documents) MUST be
  explicitly mentioned in the executive_summary.

Data:
- Vendor: {state.vendor_name} | Revenue: ${state.annual_revenue:,.0f} | Country: {state.country}
- Eligibility: {qual.get('eligible')} | Risk: {qual.get('risk_level')}
- Fraud Score: {fraud.get('fraud_score')}/100 | Fraud Flags: {fraud.get('flags', [])}
- Compliance: {comp.get('compliance_status')} | Action Items: {comp.get('action_items', [])}
- Missing Documents: {qual.get('missing_documents', [])}
- Document Verification Status: {docs.get('overall_document_status')}
- Missing Required Documents: {docs.get('missing_required_documents', [])}
- Document Findings: {docs.get('documents_checked', [])}

Respond ONLY with valid JSON.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    result = json.loads(response.content.strip().strip("```json").strip("```"))
    state.kpi_summary = result
    state.final_decision = result.get("decision", "PENDING_REVIEW")
    state.pipeline_status = "completed"
    return state
