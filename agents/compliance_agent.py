"""
Agent 3 — Compliance Reporting Agent
Auto-generates a compliance summary document for the vendor.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from .state import VendorState
import json
from datetime import date


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


def compliance_agent(state: VendorState) -> VendorState:
    qual = state.qualification_result or {}
    fraud = state.fraud_result or {}
    docs = state.document_verification_result or {}
    prompt = f"""
You are a compliance officer. Generate a structured compliance report as JSON with:
- compliance_status ("compliant" | "partially_compliant" | "non_compliant")
- regulations_checked (list of strings)
- action_items (list of strings)
- report_summary (2-3 sentence string)

Vendor: {state.vendor_name} | Country: {state.country} | Type: {state.business_type}
Qualification: eligible={qual.get('eligible')}, risk={qual.get('risk_level')}
Fraud Score: {fraud.get('fraud_score')}/100 | Recommendation: {fraud.get('recommendation')}
Documents: {state.documents_submitted}

Document Verification Findings:
- Overall document status: {docs.get('overall_document_status')}
- Missing required documents: {docs.get('missing_required_documents', [])}
- Per-document results: {docs.get('documents_checked', [])}

Regulations to check: GDPR (if EU), AML/KYC, SOX (if public), local business law.
Factor the document verification findings into your compliance assessment
(missing or invalid required documents weigh against full compliance).
Respond ONLY with valid JSON.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    result = json.loads(response.content.strip().strip("```json").strip("```"))
    result["generated_date"] = str(date.today())
    state.compliance_result = result
    return state
