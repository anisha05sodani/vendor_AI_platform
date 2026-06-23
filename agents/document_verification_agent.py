"""
Agent 0 — Document Verification Agent
Runs FIRST in the pipeline. Reads the actual content of uploaded vendor
documents, matches them against a required-document checklist, asks the LLM to
assess each present document, and produces per-document comments plus an
overall verdict that later agents (compliance, KPI) can reference.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from .state import VendorState
from .config.required_documents import get_required_documents
from .utils.document_loader import load_documents
import json


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def _assess_document(state: VendorState, label: str, doc: dict) -> dict:
    """Ask the LLM to assess a single readable document. Returns {validity, comments}."""
    prompt = f"""
You are a vendor document verification specialist. Assess the document below.
Return ONLY valid JSON with:
- validity ("valid" | "invalid" | "needs_review")
- comments (1-2 sentence explanation of your findings)

Check for: legitimacy/plausibility, completeness, internal consistency
(does the business name on the document match the vendor profile name?),
expiry/date validity if applicable, and any red flags.

Expected document type: {label}
Vendor profile name: {state.vendor_name}
Vendor country: {state.country}
Vendor business type: {state.business_type}

Document filename: {doc.get('filename')}
Extracted document text (may be truncated):
\"\"\"
{doc.get('extracted_text', '')[:4000]}
\"\"\"

Respond ONLY with valid JSON.
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result = json.loads(response.content.strip().strip("```json").strip("```"))
        return {
            "validity": result.get("validity", "needs_review"),
            "comments": result.get("comments", "No assessment returned."),
        }
    except Exception as exc:  # noqa: BLE001 - a bad LLM/JSON response must not crash the run
        return {
            "validity": "needs_review",
            "comments": f"Automated assessment could not be completed ({exc}).",
        }


def _classify_document(state: VendorState, doc: dict, required: list[dict]) -> dict:
    """Judge which required document type an uploaded file actually is.

    Reads the document's content and asks the LLM to pick the single best-matching
    required-document type. The detected type is authoritative — the document is
    counted as that type only. Returns::

        {"type": "<required key | 'other' | 'unreadable'>", "confidence": "high|medium|low"}
    """
    if doc["extraction_status"] not in ("extracted", "empty"):
        return {"type": "unreadable", "confidence": "low"}

    text = doc.get("extracted_text", "")
    valid_keys = {r["key"] for r in required}

    if not text:
        # Nothing to read — fall back to the cheap filename-based keyword guess.
        guess = doc.get("doc_type_guess", "unknown")
        return {
            "type": guess if guess in valid_keys else "other",
            "confidence": "low",
        }

    options = "\n".join(f'- {r["key"]}: {r["label"]}' for r in required)
    prompt = f"""
You are a vendor document classification specialist. Read the document below and
judge which ONE of the known document types it actually is.

Known document types (choose exactly one key, or "other" if none fit):
{options}

Decide based on the document's content (titles, headings, issuing authority,
fields present), not just the filename. Return ONLY valid JSON:
{{"document_type": "<one key from the list above, or 'other'>", "confidence": "high" | "medium" | "low"}}

Document filename: {doc.get('filename')}
Extracted document text (may be truncated):
\"\"\"
{text[:4000]}
\"\"\"

Respond ONLY with valid JSON.
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        result = json.loads(response.content.strip().strip("```json").strip("```"))
        dtype = result.get("document_type", "other")
        return {
            "type": dtype if dtype in valid_keys else "other",
            "confidence": result.get("confidence", "medium"),
        }
    except Exception:  # noqa: BLE001 - a bad LLM/JSON response must not crash the run
        guess = doc.get("doc_type_guess", "unknown")
        return {
            "type": guess if guess in valid_keys else "other",
            "confidence": "low",
        }


def _summarize(state: VendorState, documents_checked: list[dict],
               missing: list[str], overall_status: str) -> str:
    """Generate a 2-3 sentence overall assessment via the LLM."""
    prompt = f"""
You are a vendor document verification specialist. Write a concise 2-3 sentence
overall assessment of this vendor's submitted documents for leadership.

Vendor: {state.vendor_name} | Country: {state.country} | Type: {state.business_type}
Overall document status: {overall_status}
Missing required documents: {missing}
Per-document findings: {json.dumps(documents_checked)}

Respond with plain text only (no JSON, no markdown).
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception:  # noqa: BLE001
        if overall_status == "complete":
            return "All required documents were submitted and passed automated checks."
        if overall_status == "incomplete":
            return f"Document set is incomplete. Missing: {', '.join(missing) or 'unknown'}."
        return "One or more documents were flagged and require manual review."


def document_verification_agent(state: VendorState) -> VendorState:
    required = get_required_documents(state.business_type, state.country)
    loaded = load_documents(state.documents or [])

    # Judge each uploaded document's true type via the LLM and index by it, so a
    # document is counted as exactly the type it actually is (filename is only a
    # weak hint — content decides).
    by_type: dict[str, list[dict]] = {}
    for doc in loaded:
        classification = _classify_document(state, doc, required)
        doc["detected_type"] = classification["type"]
        doc["detected_confidence"] = classification["confidence"]
        by_type.setdefault(classification["type"], []).append(doc)

    documents_checked: list[dict] = []
    missing_required: list[str] = []
    flagged = False

    matched_filenames: set[str] = set()

    # 1. Evaluate every required document.
    for req in required:
        candidates = by_type.get(req["key"], [])
        if not candidates:
            documents_checked.append({
                "document_type": req["key"],
                "filename": None,
                "detected_type": req["key"],
                "detected_confidence": None,
                "status": "missing",
                "validity": "needs_review",
                "comments": f"No '{req['label']}' was submitted.",
            })
            missing_required.append(req["key"])
            continue

        doc = candidates[0]
        matched_filenames.add(doc["filename"])
        if doc["extraction_status"] not in ("extracted", "empty"):
            documents_checked.append({
                "document_type": req["key"],
                "filename": doc["filename"],
                "detected_type": doc["detected_type"],
                "detected_confidence": doc["detected_confidence"],
                "status": "unreadable",
                "validity": "needs_review",
                "comments": (
                    f"'{doc['filename']}' was submitted but could not be read "
                    f"({doc['extraction_status']})."
                ),
            })
            flagged = True
            continue

        assessment = _assess_document(state, req["label"], doc)
        if assessment["validity"] == "invalid":
            flagged = True
        documents_checked.append({
            "document_type": req["key"],
            "filename": doc["filename"],
            "detected_type": doc["detected_type"],
            "detected_confidence": doc["detected_confidence"],
            "status": "present",
            "validity": assessment["validity"],
            "comments": (
                f"Identified as '{req['label']}' "
                f"(confidence: {doc['detected_confidence']}). "
                + assessment["comments"]
            ),
        })

    # 2. Report any extra (non-required) documents that were submitted.
    for doc in loaded:
        if doc["filename"] in matched_filenames:
            continue
        readable = doc["extraction_status"] in ("extracted", "empty")
        documents_checked.append({
            "document_type": doc["detected_type"],
            "filename": doc["filename"],
            "detected_type": doc["detected_type"],
            "detected_confidence": doc["detected_confidence"],
            "status": "present" if readable else "unreadable",
            "validity": "needs_review",
            "comments": (
                f"Additional document '{doc['filename']}' "
                + ("submitted (not on required checklist)." if readable
                   else f"could not be read ({doc['extraction_status']}).")
            ),
        })
        if not readable:
            flagged = True

    # 3. Compute the overall status deterministically.
    if missing_required:
        overall_status = "incomplete"
    elif flagged:
        overall_status = "flagged"
    else:
        overall_status = "complete"

    missing_labels = [
        next((r["label"] for r in required if r["key"] == key), key)
        for key in missing_required
    ]
    summary = _summarize(state, documents_checked, missing_labels, overall_status)

    state.document_verification_result = {
        "documents_checked": documents_checked,
        "missing_required_documents": missing_labels,
        "overall_document_status": overall_status,
        "summary": summary,
    }
    return state
