"""
Shared state schema passed between all agents in the LangGraph pipeline.
"""
from typing import Optional
from pydantic import BaseModel


class VendorState(BaseModel):
    # --- Input ---
    vendor_name: str
    vendor_email: str
    business_type: str
    annual_revenue: float
    country: str
    documents_submitted: list[str]
    documents: list[str] = []  # file paths to uploaded document files

    # --- Agent Outputs ---
    document_verification_result: Optional[dict] = None
    qualification_result: Optional[dict] = None
    fraud_result: Optional[dict] = None
    compliance_result: Optional[dict] = None
    kpi_summary: Optional[dict] = None

    # --- Final ---
    final_decision: Optional[str] = None
    pipeline_status: str = "pending"
    error: Optional[str] = None
