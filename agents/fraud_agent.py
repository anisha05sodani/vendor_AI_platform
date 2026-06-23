"""
Agent 2 — Fraud Detection Agent
Flags suspicious patterns in vendor submission data.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from .state import VendorState
import json


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def fraud_detection_agent(state: VendorState) -> VendorState:
    qual = state.qualification_result or {}
    prompt = f"""
You are a fraud detection specialist. Analyze the vendor submission for anomalies and return JSON with:
- fraud_score (0-100, higher = more suspicious)
- flags (list of strings describing suspicious signals)
- recommendation ("approve" | "review" | "reject")

Vendor Profile:
- Name: {state.vendor_name}
- Country: {state.country}
- Annual Revenue: ${state.annual_revenue:,.0f}
- Business Type: {state.business_type}
- Qualification Risk Level: {qual.get('risk_level', 'unknown')}
- Missing Documents: {qual.get('missing_documents', [])}

Red-flag rules: revenue > $10M from high-risk countries, missing >2 documents, PO Box addresses.
Respond ONLY with valid JSON.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    result = json.loads(response.content.strip().strip("```json").strip("```"))
    state.fraud_result = result
    return state
