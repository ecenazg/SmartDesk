# SmartDesk — Step-by-Step Setup Guide

## What You're Building

```
Your Documents (PDF/Markdown)
        │
        ▼ ingest.py
   FAISS Vector Index
        │
        ▼ main.py
   LangChain Agent (GPT-4o)
   ┌────┴─────────────────────┐
   │                          │
   ▼                          ▼
RAG Retriever          Automation Tools
(answers questions)    (triggers webhooks)
```

---

## STEP 1 — Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click **Create new secret key**
3. Copy it — you only see it once

**Cost estimate:** ~$0.01–0.05 per conversation (GPT-4o is cheap for
low-volume use)

---

## STEP 2 — Set Up Your Environment

```bash
# Clone or copy the project folder, then:
cd smartdesk

# Create a virtual environment (keeps dependencies isolated)
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install all dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Open .env in any editor and paste your OPENAI_API_KEY
```

---

## STEP 3 — Add Your Documents

Put any PDF or Markdown files into the `docs/` folder.

A sample file (`docs/returns_sop.md`) is already included so you can
test immediately without your own documents.

**What kinds of documents work best:**
- SOPs (Standard Operating Procedures)
- FAQ documents
- Process guides
- Policy documents
- Meeting notes / briefs

---

## STEP 4 — Ingest Your Documents

This builds the FAISS vector index (your searchable knowledge base):

```bash
python ingest.py --source ./docs/
```

You'll see output like:
```
🚀 SmartDesk Ingestion Pipeline
────────────────────────────────────────
  📝 Loading Markdown: returns_sop.md
✅ Loaded 1 document pages/sections
✅ Split into 8 chunks (size=500, overlap=100)
🔄 Generating embeddings (this calls the OpenAI API)...
✅ FAISS index saved to: ./faiss_index/
```

---

## STEP 5 — Run the Agent

```bash
python main.py
```

Then try these test queries:

```
You: What is the return process for damaged shipments?
You: Create a ClickUp task to review the returns SOP next Monday
You: Send a Slack message to the ops team about the new policy
```

---

## STEP 6 — Connect Automations (Optional)

### n8n (self-hosted, free)
1. Install n8n: `npm install n8n -g && n8n start`
2. Create a workflow with a **Webhook** trigger node
3. Copy the webhook URL → paste into `.env` as `N8N_WEBHOOK_URL`
4. Add output nodes: ClickUp, Google Sheets, Slack, etc.

### Make.com (cloud, has free tier)
1. Sign up at make.com
2. Create a scenario → add **Webhooks > Custom Webhook** as trigger
3. Copy URL → paste into `.env` as `MAKE_WEBHOOK_URL`

---

## STEP 7 — Deploy to Google Cloud Run (Optional)

```bash
# Build Docker image
docker build -t smartdesk .

# Test locally
docker run -p 8080:8080 --env-file .env smartdesk

# Deploy to Cloud Run (requires gcloud CLI installed + Google account)
gcloud run deploy smartdesk \
  --image smartdesk \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=your_key_here
```

---

## Project File Map

```
smartdesk/
├── main.py                    ← START HERE — runs the agent
├── ingest.py                  ← Run once to build the knowledge base
├── requirements.txt           ← Python dependencies
├── .env.example               ← Copy to .env and fill in secrets
├── Dockerfile                 ← For Cloud Run deployment
│
├── agent/
│   ├── agent.py               ← Wires LLM + tools + memory together
│   ├── tools.py               ← What the agent can DO (search, trigger, notify)
│   └── prompts.py             ← Agent personality + tool usage rules
│
├── rag/
│   ├── retriever.py           ← Loads FAISS index, runs retrieval queries
│   └── evaluator.py          ← RAGAS scoring (faithfulness, relevance)
│
├── integrations/
│   ├── webhook.py             ← Generic n8n/Make.com webhook caller
│   └── clickup.py            ← ClickUp task creation via REST API
│
├── logging/
│   └── audit_logger.py       ← Structured JSON logging for LLMOps
│
├── docs/                      ← Put your knowledge base documents here
│   └── returns_sop.md        ← Sample document (included for testing)
│
└── logs/
    └── audit.jsonl           ← Auto-created; one JSON entry per agent turn
```

---

## Common Issues

**"FAISS index not found"**
→ You need to run `python ingest.py --source ./docs/` first.

**"OPENAI_API_KEY not set"**
→ Make sure you copied `.env.example` to `.env` and filled in the key.

**"No documents found"**
→ Make sure your files end in `.pdf` or `.md` and are inside `./docs/`.

**Webhook returns 404**
→ Double-check the webhook URL in `.env`. For n8n, make sure the
  workflow is **activated** (not just saved).

---

## What's Next (Recommended Order)

1. ✅ Get it running with the sample document
2. 📄 Add your own documents and re-run ingest.py
3. 🔗 Connect one webhook (n8n or Make.com)
4. 📊 Check `logs/audit.jsonl` after a few queries
5. 🔑 Add Langfuse for visual observability (free tier)
6. 🐳 Deploy to Cloud Run
