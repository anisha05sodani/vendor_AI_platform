"""
Agent 4 — Executive KPI Summary Agent

The final decision and overall score are computed **deterministically in Python**
from explicit rules (LLMs do not reliably follow numeric thresholds). The LLM is
used only to write the executive narrative (summary + next steps).
"""
from .state import VendorState
from .utils.llm import get_llm, invoke_json


# Low-temperature client; JSON mode for the narrative payload.
llm = get_llm(temperature=0.2)


def _missing_docs_count(qual: dict, docs: dict) -> int:
    """Authoritative missing-document count.

    Prefers the document-verification agent's findings (content-based), falling
    back to the qualification agent's profile-based list.
    """
    dv_missing = docs.get("missing_required_documents")
    if dv_missing is not None:
        return len(dv_missing)
    return len(qual.get("missing_documents") or [])


def _decide(qual: dict, fraud: dict, comp: dict, docs: dict) -> str:
    """Deterministic final decision. Hard rules enforced in Python."""
    eligible = qual.get("eligible")
    risk = qual.get("risk_level")
    fraud_score = fraud.get("fraud_score", 0) or 0
    compliance_status = comp.get("compliance_status")
    doc_status = docs.get("overall_document_status")
    missing_count = _missing_docs_count(qual, docs)

    # --- Hard reject rules ---
    if fraud_score >= 85 or eligible is False or compliance_status == "non_compliant":
        return "REJECTED"

    # --- Approval requires every condition to hold ---
    if (
        eligible is True
        and risk == "low"
        and fraud_score < 40
        and compliance_status in ("compliant", "partially_compliant")
        and missing_count <= 1
        and doc_status == "complete"
    ):
        return "APPROVED"

    return "PENDING_REVIEW"


def _overall_score(qual: dict, fraud: dict, comp: dict, docs: dict) -> int:
    """Deterministic 0-100 health score from weighted penalties."""
    score = 100.0
    score -= (fraud.get("fraud_score", 0) or 0) * 0.4  # up to -40
    score -= {"low": 0, "medium": 15, "high": 35}.get(qual.get("risk_level"), 20)
    score -= {
        "compliant": 0,
        "partially_compliant": 15,
        "non_compliant": 45,
    }.get(comp.get("compliance_status"), 20)
    score -= {
        "complete": 0,
        "flagged": 15,
        "incomplete": 25,
    }.get(docs.get("overall_document_status"), 15)
    score -= _missing_docs_count(qual, docs) * 5
    if qual.get("eligible") is False:
        score -= 40
    return max(0, min(100, round(score)))


def _narrative(state: VendorState, decision: str, overall_score: int,
               qual: dict, fraud: dict, comp: dict, docs: dict) -> dict:
    """Ask the LLM to write prose only — it does NOT decide the outcome."""
    prompt = f"""
You are an executive assistant writing a leadership briefing. The DECISION and
SCORE have already been determined; do NOT change them. Return ONLY valid JSON:
- executive_summary (3-4 sentence string for leadership)
- next_steps (list of action strings)

Decision (final, do not change): {decision}
Overall score (final, do not change): {overall_score}/100

Data:
- Vendor: {state.vendor_name} | Revenue: ${state.annual_revenue:,.0f} | Country: {state.country}
- Eligibility: {qual.get('eligible')} | Risk: {qual.get('risk_level')}
- Fraud Score: {fraud.get('fraud_score')}/100 | Fraud Flags: {fraud.get('flags', [])}
- Compliance: {comp.get('compliance_status')} | Action Items: {comp.get('action_items', [])}
- Document Verification Status: {docs.get('overall_document_status')}
- Missing Required Documents: {docs.get('missing_required_documents', [])}
- Document Findings: {docs.get('documents_checked', [])}

Any document concern (missing/invalid/unreadable required documents) MUST be
mentioned in the executive_summary. Respond ONLY with valid JSON.
"""
    try:
        result = invoke_json(llm, prompt)
        return {
            "executive_summary": result.get("executive_summary", ""),
            "next_steps": result.get("next_steps", []),
        }
    except Exception as exc:  # noqa: BLE001 - narrative failure must not crash the run
        state.error = f"KPI narrative generation failed: {exc}"
        return {
            "executive_summary": (
                f"Decision: {decision} (score {overall_score}/100). "
                "Automated executive summary could not be generated; "
                "see individual agent results."
            ),
            "next_steps": ["Manual review of the vendor file is recommended."],
        }


def kpi_agent(state: VendorState) -> VendorState:
    qual = state.qualification_result or {}
    fraud = state.fraud_result or {}
    comp = state.compliance_result or {}
    docs = state.document_verification_result or {}

    decision = _decide(qual, fraud, comp, docs)
    overall_score = _overall_score(qual, fraud, comp, docs)
    key_metrics = {
        "risk_level": qual.get("risk_level"),
        "fraud_score": fraud.get("fraud_score"),
        "compliance_status": comp.get("compliance_status"),
        "missing_docs_count": _missing_docs_count(qual, docs),
        "document_status": docs.get("overall_document_status"),
    }

    narrative = _narrative(state, decision, overall_score, qual, fraud, comp, docs)

    state.kpi_summary = {
        "overall_score": overall_score,
        "decision": decision,
        "key_metrics": key_metrics,
        "executive_summary": narrative["executive_summary"],
        "next_steps": narrative["next_steps"],
    }
    state.final_decision = decision
    state.pipeline_status = "completed"
    return state
