"""
Agent 2 — Fraud Detection Agent
Flags suspicious patterns in vendor submission data.
"""
from .state import VendorState
from .utils.llm import get_llm, invoke_json


llm = get_llm(temperature=0)


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
    try:
        result = invoke_json(llm, prompt)
    except Exception as exc:  # noqa: BLE001 - a bad LLM/JSON response must not crash the run
        state.error = f"Fraud agent failed: {exc}"
        result = {
            "fraud_score": 50,
            "flags": [f"Automated fraud analysis could not be completed ({exc})."],
            "recommendation": "review",
        }
    state.fraud_result = result
    return state
