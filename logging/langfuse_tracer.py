"""
logging/langfuse_tracer.py — Langfuse Observability
──────────────────────────────────────────────────────
WHAT IS LANGFUSE?
  Langfuse is a free, open-source LLMOps platform.
  It gives you a visual dashboard showing:
  - Every agent trace (full reasoning chain, tool calls, token counts)
  - Latency per step
  - Cost per query
  - RAGAS scores over time
  - Which tools are called most often

WHY THIS MATTERS FOR YOUR CV:
  "Implemented distributed tracing with Langfuse" — this is exactly
  what production AI teams do to monitor models in deployment.

SETUP (free):
  1. Sign up at https://cloud.langfuse.com (free tier, no credit card)
  2. Create a project → copy Public Key + Secret Key
  3. Add to .env:
       LANGFUSE_PUBLIC_KEY=pk-lf-...
       LANGFUSE_SECRET_KEY=sk-lf-...
       LANGFUSE_HOST=https://cloud.langfuse.com

  Then every agent call will appear in your Langfuse dashboard automatically.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_langfuse_callback():
    """
    Returns a LangChain callback handler that sends traces to Langfuse.
    Returns None if Langfuse is not configured (agent still works fine).

    Usage in agent.py:
        from logging.langfuse_tracer import get_langfuse_callback
        callbacks = [cb for cb in [get_langfuse_callback()] if cb]
        result = executor.invoke({"input": user_input}, config={"callbacks": callbacks})
    """
    public_key  = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key  = os.getenv("LANGFUSE_SECRET_KEY", "")
    host        = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        return None  # silently skip — Langfuse is optional

    try:
        from langfuse.callback import CallbackHandler
        handler = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        print("✅ Langfuse tracing enabled")
        return handler
    except ImportError:
        print("⚠️  langfuse not installed. Run: pip install langfuse")
        return None
    except Exception as e:
        print(f"⚠️  Langfuse init failed: {e}")
        return None


def log_rag_score_to_langfuse(trace_id: str, scores: dict):
    """
    Attach RAGAS scores to a Langfuse trace as a 'score' event.
    This lets you filter and sort traces by retrieval quality in the dashboard.

    Args:
        trace_id: The Langfuse trace ID (returned by CallbackHandler)
        scores:   Dict with 'faithfulness' and 'answer_relevancy' keys
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")

    if not public_key:
        return

    try:
        from langfuse import Langfuse
        lf = Langfuse(public_key=public_key, secret_key=secret_key)

        for metric_name, value in scores.items():
            if value is not None:
                lf.score(
                    trace_id=trace_id,
                    name=metric_name,
                    value=value,
                )
    except Exception as e:
        print(f"⚠️  Failed to log RAGAS score to Langfuse: {e}")
