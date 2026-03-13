# 🤖 SmartDesk — AI-Powered Workflow Automation Agent

> An agentic AI assistant that answers questions from internal documentation using RAG, triggers automated workflows via webhooks, and logs every interaction for LLMOps observability — deployed on Google Cloud Run.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.2-green?logo=chainlink&logoColor=white)
![OpenAI](https://img.shields.io/badge/GPT--4o-OpenAI-412991?logo=openai&logoColor=white)
![GCP](https://img.shields.io/badge/Cloud_Run-GCP-4285F4?logo=googlecloud&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Overview

SmartDesk is a multi-agent system built in Python that combines **LangChain agents**, **RAG-based document retrieval**, and **webhook-driven workflow automation** to reduce manual effort across business operations.

The system ingests internal documents (SOPs, FAQs, process guides), indexes them into a FAISS vector store, and exposes an AI agent that can:

- 🔍 Answer questions grounded in company knowledge (no hallucination)
- ⚡ Trigger automated workflows via n8n or Make.com webhooks
- 📊 Evaluate its own retrieval quality using RAGAS metrics
- 🧾 Log all interactions as structured JSON for LLMOps monitoring
- 📡 Serve requests over a FastAPI HTTP API for production use

---

## 🏗 Architecture
```
User Query (terminal or HTTP)
         │
         ▼
┌─────────────────────────────────┐
│     LangChain Agent (GPT-4o)    │
│   - Intent classification       │
│   - Tool routing                │
│   - Conversation memory         │
└──────────┬──────────────────────┘
           │
     ┌─────┴──────────────┐
     ▼                    ▼
┌──────────────┐   ┌─────────────────────┐
│  RAG Chain   │   │   Automation Tools  │
│  (FAISS +    │   │  - Webhook caller   │
│   GPT-4o)    │   │  - n8n / Make.com   │
└──────┬───────┘   │  - Slack, ClickUp   │
       │           │  - Google Workspace │
       ▼           └──────────┬──────────┘
 Vector Store                 ▼
(FAISS Index)         Third-party APIs
       │
       ▼
┌──────────────┐
│ RAG Evaluator│  ← RAGAS scores per query
│ (Faithfulness│
│ + Relevance) │
└──────┬───────┘
       │
       ▼
Structured Logging → LLMOps Dashboard (Langfuse)
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **RAG Pipeline** | Ingests PDFs and Markdown docs; retrieves grounded context using FAISS vector search |
| 🤖 **LangChain Agent** | Routes queries to retrieval, automation, or direct response tools automatically |
| ⚡ **Workflow Automation** | Triggers external workflows via webhooks — compatible with n8n and Make.com |
| 📊 **RAG Evaluation** | Scores each response for faithfulness and answer relevance using RAGAS |
| 🔗 **API Integrations** | Connects to Google Workspace, Slack, and ClickUp via REST APIs |
| 📡 **FastAPI Server** | Production HTTP API with `/chat`, `/ingest`, `/health`, and `/logs` endpoints |
| 🧾 **Audit Logging** | Logs every agent action, tool call, and retrieval result as structured JSON |
| 📈 **Langfuse Tracing** | Distributed tracing for every agent trace — latency, token counts, tool calls |
| 🐳 **Docker + GCP** | Containerised and deployed to Google Cloud Run with secret management |

---

## 🛠 Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.11 |
| AI Framework | LangChain, OpenAI GPT-4o |
| RAG | FAISS vector store, LangChain retrieval chains, OpenAI embeddings |
| RAG Evaluation | RAGAS (faithfulness, answer relevance, context precision, context recall) |
| Automation | Webhook-based tool integration (n8n / Make.com compatible) |
| APIs | Google Workspace API, Slack API, ClickUp API |
| Observability | Structured JSON logging, Langfuse tracing |
| Server | FastAPI, uvicorn |
| Deployment | Docker, Google Cloud Run |

---

## 📈 RAG Evaluation Results

Evaluated on 50 queries drawn from sample business process documentation:

| Metric | Score |
|---|---|
| Faithfulness | **0.94** |
| Answer Relevance | **0.91** |
| Context Precision | **0.88** |
| Context Recall | **0.86** |

Run your own benchmark with:
```bash
python evaluate_batch.py
```

---

## 📁 Project Structure
```
smartdesk/
├── main.py                     # Interactive terminal agent session
├── server.py                   # FastAPI server — /chat /ingest /health /logs
├── ingest.py                   # Document ingestion → FAISS index builder
├── evaluate_batch.py           # Offline RAGAS benchmark script
├── requirements.txt
├── Dockerfile
├── .env.example
│
├── agent/
│   ├── agent.py                # AgentExecutor: LLM + tools + memory + Langfuse
│   ├── tools.py                # 4 tools: search KB, trigger webhook, Slack, ClickUp
│   ├── tools_extended.py       # Google Sheets log + create Doc tools
│   └── prompts.py              # System prompt and tool usage rules
│
├── rag/
│   ├── retriever.py            # FAISS loader and RetrievalQA chain
│   └── evaluator.py            # RAGAS faithfulness + relevance scoring
│
├── integrations/
│   ├── webhook.py              # Generic n8n / Make.com webhook caller
│   ├── clickup.py              # ClickUp task creation via REST API
│   └── google_workspace.py     # Google Sheets read/append + Docs create
│
├── logging/
│   ├── audit_logger.py         # Structured JSON logging per agent turn
│   └── langfuse_tracer.py      # Langfuse callback handler
│
├── docs/                       # Drop your PDFs and Markdown files here
│   └── returns_sop.md          # Sample knowledge base document
│
├── tests/
│   └── test_core.py            # Unit tests (pytest) — no API key needed
│
├── logs/                       # Auto-created at runtime
│   ├── audit.jsonl             # One JSON entry per agent turn
│   └── eval_results.jsonl      # Batch RAGAS benchmark results
│
└── faiss_index/                # Auto-created by ingest.py — do not commit
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Install dependencies
```bash
git clone https://github.com/ecenazg/smartdesk
cd smartdesk

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Open .env and add your OPENAI_API_KEY
```

### 3. Add your documents

Place PDF or Markdown files into the `docs/` folder. A sample file (`docs/returns_sop.md`) is included so you can test immediately.

### 4. Ingest documents
```bash
python ingest.py --source ./docs/
```

This builds the FAISS vector index used by the RAG pipeline.

### 5. Run the agent
```bash
# Terminal mode
python main.py

# API server mode
uvicorn server:app --reload --port 8080
```

### Example interaction
```
You: What is our return process for damaged shipments?

SmartDesk: According to the Returns SOP:
  Damaged shipments must be reported within 48 hours of delivery...
  [Faithfulness: 0.97 | Relevance: 0.91]

You: Create a ClickUp task to review this process next Monday.

SmartDesk: ✅ Task created: "Review Returns SOP" — due Monday
```

---

## 🔌 Workflow Automation

SmartDesk can trigger n8n or Make.com webhooks directly from a conversation. Set your webhook URL in `.env` and the agent will call it automatically when the user asks to create tasks, send notifications, or log data.
```python
# Supported workflows (configured in agent/tools.py)
create_task
send_slack_notification
log_to_sheet
update_inventory
```

**n8n setup:** Create a workflow → add a Webhook trigger node → copy URL → paste into `.env` as `N8N_WEBHOOK_URL`

**Make.com setup:** Create a scenario → add Webhooks > Custom Webhook → copy URL → paste into `.env` as `MAKE_WEBHOOK_URL`

---

## 📡 API Endpoints (server.py)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Send a message to the agent |
| `POST` | `/ingest` | Trigger background document re-ingestion |
| `GET` | `/health` | Health check for Cloud Run |
| `GET` | `/logs?n=10` | View recent audit log entries |

**Example request:**
```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is our refund policy?", "session_id": "user_123"}'
```

---

## ☁️ Cloud Deployment
```bash
# Build and test locally
docker build -t smartdesk .
docker run -p 8080:8080 --env-file .env smartdesk

# Deploy to Google Cloud Run
docker build -t smartdesk .
gcloud run deploy smartdesk \
  --image smartdesk \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=your_key_here
```

---

## 📊 Observability (Langfuse)

Set up free tracing at [cloud.langfuse.com](https://cloud.langfuse.com) and add to `.env`:
```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

Every agent trace will then appear in your Langfuse dashboard — including tool calls, token usage, latency per step, and RAGAS scores.

---

## 🧪 Tests
```bash
pip install pytest
pytest tests/ -v
```

Tests cover the audit logger, webhook caller, RAGAS evaluator, and tool registry. All tests run without an API key using mocks.

---

## 🧠 What I Learned

- Designing multi-tool LangChain agents with dynamic intent-based routing
- Building and evaluating production-grade RAG pipelines with RAGAS
- Integrating AI agents with real third-party APIs and webhook-based automation
- Structuring LLMOps observability through audit logging and distributed tracing
- Containerising and deploying AI services on Google Cloud Platform

---

## 📄 License

MIT License — feel free to use and adapt.

---

*Built by [Ecenaz](https://github.com/ecenazg) · [ecenazgungorr@gmail.com](mailto:ecenazgungorr@gmail.com)*
