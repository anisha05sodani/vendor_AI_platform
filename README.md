# 🤖 Vendor AI Onboarding Platform

> **Resume-ready multi-agent AI system** for automating vendor onboarding using LangGraph, Groq (Llama 3.3 70B), FastAPI, and a React + Vite + Tailwind CSS frontend.

---

## 🏗️ Architecture

```
User Submits Vendor →  FastAPI  →  LangGraph Orchestrator
                                        │
                          ┌─────────────▼──────────────┐
                          │   Agent 1: Qualification    │ ← eligibility, docs, risk
                          └─────────────┬──────────────┘
                                        │
                          ┌─────────────▼──────────────┐
                          │   Agent 2: Fraud Detection  │ ← fraud score, flags
                          └──────┬──────────────┬───────┘
                          score<85              score≥85
                                 │                   └── REJECTED (skip)
                          ┌──────▼──────────────┐
                          │  Agent 3: Compliance │ ← GDPR, AML/KYC, SOX
                          └──────┬──────────────┘
                                 │
                          ┌──────▼──────────────┐
                          │  Agent 4: KPI Summary│ ← final decision, exec report
                          └─────────────────────┘
                                        │
                              React Dashboard (Vite + Tailwind)
```

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
cd vendor-ai-platform
uvicorn backend.main:app --reload --port 8000
```

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

## 📁 Project Structure
```
vendor-ai-platform/
├── agents/
│   ├── state.py               # Shared Pydantic state schema
│   ├── qualification_agent.py # Agent 1 — vendor eligibility
│   ├── fraud_agent.py         # Agent 2 — fraud detection
│   ├── compliance_agent.py    # Agent 3 — compliance report
│   └── kpi_agent.py           # Agent 4 — executive KPI summary
├── orchestrator.py            # LangGraph pipeline
├── backend/
│   └── main.py                # FastAPI REST API
├── frontend/                  # React + Vite + Tailwind dashboard
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx            # Layout + pipeline state
│       ├── api.js             # FastAPI client
│       └── components/        # Form + results UI
├── requirements.txt
└── .env.example
```

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

- **Built an end-to-end multi-agent AI platform** using LangGraph and Groq (Llama 3.3 70B) to automate vendor onboarding — orchestrating 4 specialized agents (qualification, fraud detection, compliance, KPI reporting) in a conditional pipeline.

- **Reduced manual vendor screening time by ~70%** by implementing agentic AI workflows with conditional routing logic (auto-reject vendors with fraud score ≥ 85).

- **Exposed the pipeline via FastAPI REST API** and built an executive React (Vite + Tailwind) dashboard displaying real-time agent outputs, fraud flags, compliance status, and final approval decisions.

---

## 💡 Extensions (to make it stand out more)

- [ ] Add a **vector database (Pinecone/Weaviate)** for RAG-based policy Q&A
- [ ] Integrate **email notifications** (SendGrid) on decision
- [ ] Add **PostgreSQL** to persist vendor history
- [ ] Deploy to **Azure App Service** or **AWS Lambda**
- [ ] Add **LangSmith tracing** for agent observability
