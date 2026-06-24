"""
Agent 1 — Vendor Qualification Agent
Screens vendor eligibility based on submitted profile data.
"""
from .state import VendorState
from .config.required_documents import get_required_documents
from .utils.llm import get_llm, invoke_json


llm = get_llm(temperature=0)


def vendor_qualification_agent(state: VendorState) -> VendorState:
    # Single source of truth: the required-document checklist comes from
    # agents/config/required_documents.py (shared with the verification agent
    # and the frontend), not a hardcoded list.
    required_labels = [
        r["label"] for r in get_required_documents(state.business_type, state.country)
    ]
    prompt = f"""
You are a vendor qualification specialist. Evaluate the following vendor and return a JSON with:
- eligible (bool)
- risk_level ("low" | "medium" | "high")
- reason (string)
- missing_documents (list of strings)

Vendor Profile:
- Name: {state.vendor_name}
- Business Type: {state.business_type}
- Annual Revenue: ${state.annual_revenue:,.0f}
- Country: {state.country}
- Documents Submitted: {', '.join(state.documents_submitted)}

Required documents: {required_labels}
Respond ONLY with valid JSON.
"""
    try:
        result = invoke_json(llm, prompt)
    except Exception as exc:  # noqa: BLE001 - a bad LLM/JSON response must not crash the run
        state.error = f"Qualification agent failed: {exc}"
        result = {
            "eligible": None,
            "risk_level": "high",
            "reason": (
                "Automated qualification could not be completed "
                f"({exc}). Manual review required."
            ),
            "missing_documents": [],
        }
    state.qualification_result = result
    return state
