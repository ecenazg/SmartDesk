"""
server.py — SmartDesk FastAPI Server
──────────────────────────────────────
WHY A SERVER INSTEAD OF JUST main.py?
  The terminal loop in main.py is great for local testing, but in
  production you need an HTTP API so that:
  - n8n / Make.com can CALL SmartDesk (not just be called by it)
  - A frontend or Slack bot can send messages to the agent
  - Cloud Run has a real health-check endpoint
  - Multiple users can query the agent concurrently

ENDPOINTS:
  POST /chat          — Send a message to the agent
  POST /ingest        — Trigger document re-ingestion
  GET  /health        — Health check (Cloud Run needs this)
  GET  /logs          — View recent audit log entries

USAGE:
  pip install fastapi uvicorn
  uvicorn server:app --reload --port 8080
"""

import os
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

# ── Global agent state ────────────────────────────────────────────────────────
# The agent is expensive to initialize (loads FAISS, connects to OpenAI).
# We build it once at startup and reuse it for every request.

_agent_executor = None
_audit_logger   = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the agent when the server starts."""
    global _agent_executor, _audit_logger

    print("🚀 SmartDesk server starting...")
    from agent.agent import build_agent
    from logging.audit_logger import AuditLogger

    _agent_executor = build_agent()
    _audit_logger   = AuditLogger(session_id="server")
    print("✅ Agent ready — server is live\n")

    yield  # server runs here

    print("SmartDesk server shutting down.")


app = FastAPI(
    title="SmartDesk API",
    description="AI-powered workflow automation agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow requests from any origin (tighten this in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"   # future: per-user session isolation

class ChatResponse(BaseModel):
    response: str
    latency_ms: int
    session_id: str

class IngestRequest(BaseModel):
    source_dir: str = "./docs/"

class IngestResponse(BaseModel):
    status: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the SmartDesk agent.

    Example request body:
      { "message": "What is our return policy?", "session_id": "user_123" }
    """
    if not _agent_executor:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    from agent.agent import run_agent

    start = time.time()
    _audit_logger.log_input(request.message)

    try:
        response = run_agent(_agent_executor, request.message, _audit_logger)
    except Exception as e:
        _audit_logger.log_error(e, context=request.message)
        raise HTTPException(status_code=500, detail=str(e))

    latency_ms = round((time.time() - start) * 1000)

    return ChatResponse(
        response=response,
        latency_ms=latency_ms,
        session_id=request.session_id,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Trigger document re-ingestion in the background.
    Returns immediately — ingestion runs async.

    Use this when you add new documents and want to update the knowledge base
    without restarting the server.
    """
    def run_ingestion():
        from ingest import load_documents, split_documents, build_faiss_index
        try:
            docs   = load_documents(request.source_dir)
            chunks = split_documents(docs)
            build_faiss_index(chunks, "./faiss_index")
            print(f"✅ Background ingestion complete: {len(chunks)} chunks indexed")
        except Exception as e:
            print(f"❌ Background ingestion failed: {e}")

    background_tasks.add_task(run_ingestion)

    return IngestResponse(
        status="accepted",
        message=f"Ingestion started for '{request.source_dir}'. "
                "Check server logs for progress."
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint — Cloud Run pings this before routing traffic.
    Returns 200 if the agent is ready.
    """
    return {
        "status":        "healthy",
        "agent_ready":   _agent_executor is not None,
        "timestamp":     time.time(),
    }


@app.get("/logs")
async def get_recent_logs(n: int = 10):
    """Return the N most recent audit log entries."""
    from logging.audit_logger import tail_logs
    logs = tail_logs(n)
    return {"count": len(logs), "logs": logs}


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)