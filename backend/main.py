"""
FastAPI Backend — exposes the agent pipeline via REST API.
"""
from dotenv import load_dotenv
load_dotenv()  # Load GROQ_API_KEY from .env

import json
import os
import shutil
import tempfile

# Validate required configuration BEFORE importing the agent pipeline. The
# agents instantiate ChatGroq at import time, so a missing key would otherwise
# crash here with a cryptic error instead of a clear, actionable message.
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError(
        "GROQ_API_KEY is not set. Create a .env file at the project root "
        "(copy .env.example) and add your Groq API key before starting the "
        "server."
    )

from fastapi import FastAPI, HTTPException, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from orchestrator import run_pipeline
from agents.config.required_documents import get_required_documents

app = FastAPI(
    title="Vendor AI Orchestration Platform",
    description="Multi-agent pipeline for vendor onboarding automation",
    version="1.0.0",
)


# CORS: in development the Vite dev server proxies /api/* to this backend, so no
# CORS handling is needed. For production, set ALLOWED_ORIGINS to a comma-
# separated list of trusted frontend origins (e.g.
# "https://app.example.com,https://admin.example.com").
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class VendorRequest(BaseModel):
    vendor_name: str
    vendor_email: str
    business_type: str
    annual_revenue: float
    country: str
    documents_submitted: list[str]


class PipelineResponse(BaseModel):
    pipeline_status: str
    final_decision: Optional[str]
    document_verification_result: Optional[dict]
    qualification_result: Optional[dict]
    fraud_result: Optional[dict]
    compliance_result: Optional[dict]
    kpi_summary: Optional[dict]
    error: Optional[str]


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Vendor AI Platform"}


@app.post("/api/v1/onboard", response_model=PipelineResponse)
def onboard_vendor(
    vendor_name: str = Form(...),
    vendor_email: str = Form(...),
    business_type: str = Form(...),
    annual_revenue: float = Form(...),
    country: str = Form(...),
    documents_submitted: str = Form("[]"),
    files: list[UploadFile] = File(default=[]),
):
    """
    Runs the full agent pipeline on multipart form data:
    Document Verification → Qualification → Fraud Detection → Compliance → KPI Summary

    `documents_submitted` is a JSON-encoded list of document names. NOTE: this
    legacy text checklist is **deprecated** — the Document Verification agent now
    reads the actual uploaded `files`, which is the authoritative signal. It is
    retained only for backward compatibility and may be removed in future.

    SCALING NOTE: this is a synchronous (blocking) endpoint and the pipeline
    (LLM calls + OCR/PDF parsing) can take ~20-30s, holding a worker thread for
    the whole request. Fine for a demo; for production move to an async
    endpoint + background task/queue (e.g. Celery/RQ) and stream results.
    """
    # Parse the legacy text checklist.
    try:
        docs_submitted = json.loads(documents_submitted)
        if not isinstance(docs_submitted, list):
            docs_submitted = [str(docs_submitted)]
    except (json.JSONDecodeError, TypeError):
        docs_submitted = [documents_submitted] if documents_submitted else []

    # Save uploaded files to a per-request temp directory.
    tmp_dir = tempfile.mkdtemp(prefix="vendor_docs_")
    saved_paths: list[str] = []
    try:
        for upload in files:
            if not upload or not upload.filename:
                continue
            safe_name = os.path.basename(upload.filename)
            dest = os.path.join(tmp_dir, safe_name)
            with open(dest, "wb") as out_file:
                shutil.copyfileobj(upload.file, out_file)
            saved_paths.append(dest)

        vendor_data = {
            "vendor_name": vendor_name,
            "vendor_email": vendor_email,
            "business_type": business_type,
            "annual_revenue": annual_revenue,
            "country": country,
            "documents_submitted": docs_submitted,
            "documents": saved_paths,
        }
        result = run_pipeline(vendor_data)
        return PipelineResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.get("/api/v1/sample")
def get_sample_payload():
    """Returns a sample vendor payload for testing."""
    return {
        "vendor_name": "TechNova Solutions Ltd",
        "vendor_email": "contact@technova.com",
        "business_type": "IT Services",
        "annual_revenue": 2500000,
        "country": "India",
        "documents_submitted": ["Business Registration", "Tax Certificate", "ID Proof"],
    }


@app.get("/api/v1/required-documents")
def required_documents(
    business_type: Optional[str] = None,
    country: Optional[str] = None,
):
    """Single source of truth for the document checklist.

    Returns the required-document keys/labels from
    ``agents/config/required_documents.py`` so the frontend and the agents all
    agree on one canonical list (optionally tailored by business type/country).
    """
    docs = get_required_documents(business_type, country)
    return {
        "required_documents": [
            {"key": d["key"], "label": d["label"]} for d in docs
        ]
    }


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
