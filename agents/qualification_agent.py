"""
Agent 1 — Vendor Qualification Agent
Screens vendor eligibility based on submitted profile data.
"""
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from .state import VendorState
import json, os


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


def vendor_qualification_agent(state: VendorState) -> VendorState:
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

Required documents: ["Business Registration", "Tax Certificate", "Bank Statement", "ID Proof"]
Respond ONLY with valid JSON.
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    result = json.loads(response.content.strip().strip("```json").strip("```"))
    state.qualification_result = result
    return state
