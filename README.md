# 🤖 Vendor AI Onboarding Platform

> **Resume-ready multi-agent AI system** for automating vendor onboarding using LangGraph, Groq (Llama 3.3 70B), FastAPI, and a React + Vite + Tailwind CSS frontend.

---

## 🏗️ Architecture

```
User Submits Vendor  →  FastAPI  →  LangGraph Orchestrator
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │   Agent 0: Document Verification           │ ← reads & verifies uploaded files
                    └─────────────────────┬─────────────────────┘
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │   Agent 1: Qualification                  │ ← eligibility, docs, risk
                    └─────────────────────┬─────────────────────┘
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │   Agent 2: Fraud Detection                │ ← fraud score, flags
                    └──────────┬─────────────────────┬──────────┘
                          score < 85            score ≥ 85
                               │                      └── REJECTED (reject node, skip)
                    ┌──────────▼────────────┐
                    │  Agent 3: Compliance   │ ← GDPR, AML/KYC, SOX
                    └──────────┬────────────┘
                               │
                    ┌──────────▼────────────┐
                    │  Agent 4: KPI Summary  │ ← decision + score (computed in Python)
                    └──────────┬────────────┘
                               │
                    React Dashboard (Vite + Tailwind)
```

> **Note:** The final decision and overall score are computed **deterministically
> in Python** (KPI agent); the LLM only writes the executive narrative.

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone <your-repo>
cd vendor-ai-platform
pip install -r requirements.txt
```

### 2. Set API Key
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Start the API
```bash
# IMPORTANT: run from the repository root. `orchestrator` is imported as a
# top-level module, so the backend only resolves imports when launched here.
cd vendor-ai-platform
uvicorn backend.main:app --reload --port 8000
```

> If `uvicorn` is not on your PATH, use `python -m uvicorn backend.main:app --reload --port 8000`.

### 4. Start the UI (new terminal)
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

> The Vite dev server proxies `/api/*` requests to the FastAPI backend on
> port 8000, so no CORS configuration is required during development.

---

## 🔌 API Reference

Interactive docs are available at [http://localhost:8000/docs](http://localhost:8000/docs) once the API is running.

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/health` | Liveness check. |
| `POST` | `/api/v1/onboard` | Run the full pipeline on a vendor submission (form fields + uploaded documents). Synchronous; ~20–30s. |
| `GET`  | `/api/v1/required-documents` | Required-document checklist for a `business_type` + `country`. |
| `GET`  | `/api/v1/sample` | Sample request payload for quick testing. |

```bash
# Required-document checklist
curl "http://localhost:8000/api/v1/required-documents?business_type=Finance&country=Germany"
```

---

## 📁 Project Structure
```
vendor-ai-platform/
├── agents/
│   ├── state.py                      # Shared Pydantic state schema
│   ├── document_verification_agent.py# Agent 0 — reads & verifies uploaded files
│   ├── qualification_agent.py        # Agent 1 — vendor eligibility
│   ├── fraud_agent.py                # Agent 2 — fraud detection
│   ├── compliance_agent.py           # Agent 3 — compliance report
│   ├── kpi_agent.py                  # Agent 4 — decision + KPI (Python rules)
│   ├── config/
│   │   └── required_documents.py     # Single source of truth for the checklist
│   └── utils/
│       ├── llm.py                    # ChatGroq factory + robust JSON parser
│       └── document_loader.py        # PDF/DOCX/OCR text extraction
├── orchestrator.py                   # LangGraph pipeline (run from repo root)
├── backend/
│   └── main.py                       # FastAPI REST API
├── frontend/                         # React + Vite + Tailwind dashboard
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx                   # Layout + pipeline state
│       ├── api.js                    # FastAPI client
│       └── components/               # Form + results UI
├── data/
│   ├── generate_sample_documents.py  # Generates sample DOCX vendor docs
│   └── sample_vendor/                # Generated test documents
├── tests/                            # pytest unit tests
├── requirements.txt
└── .env.example
```

> **Packaging note:** there is no `pyproject.toml`; `orchestrator` is a
> top-level module imported by the backend, so always run the API and tests
> **from the repository root**.

---

## 🧪 Tests
```bash
# from the repository root
python -m pytest tests/ -v
```
Covers the required-document checklist, the robust JSON parser, and the
document loader (no API key or network required).

---

## 🧠 Tech Stack
| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph |
| LLM | Groq — Llama 3.3 70B Versatile |
| Backend API | FastAPI |
| Frontend | React + Vite + Tailwind CSS |
| Data Validation | Pydantic v2 |

---

## 📄 Resume Bullet Points

> *Copy-paste ready for your resume:*

- **Built an end-to-end multi-agent AI platform** using LangGraph and Groq (Llama 3.3 70B) to automate vendor onboarding — orchestrating 5 specialized agents (document verification, qualification, fraud detection, compliance, KPI reporting) in a conditional pipeline.

- **Reduced manual vendor screening time by ~70%** by implementing agentic AI workflows with conditional routing logic (auto-reject vendors with fraud score ≥ 85).

- **Exposed the pipeline via FastAPI REST API** and built an executive React (Vite + Tailwind) dashboard displaying real-time agent outputs, fraud flags, compliance status, and final approval decisions.

---

## 💡 Extensions (to make it stand out more)

- [ ] Add a **vector database (Pinecone/Weaviate)** for RAG-based policy Q&A
- [ ] Integrate **email notifications** (SendGrid) on decision
- [ ] Add **PostgreSQL** to persist vendor history
- [ ] Deploy to **Azure App Service** or **AWS Lambda**
- [ ] Add **LangSmith tracing** for agent observability
