"""
logging/audit_logger.py — Structured LLMOps Logging
──────────────────────────────────────────────────────
WHAT THIS FILE DOES:
  Logs every agent interaction as structured JSON.
  This is the foundation of LLMOps — you can't improve what you don't measure.

WHY STRUCTURED JSON LOGGING?
  Plain text logs are hard to analyze. JSON logs can be ingested by
  Langfuse, Datadog, or even a simple spreadsheet to answer questions like:
  - Which tool gets called most often?
  - What's the average response latency?
  - Which queries return low RAGAS scores?

OUTPUT:
  Logs are written to ./logs/audit.jsonl (JSON Lines format — one JSON
  object per line, easy to stream and parse).
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


LOG_DIR = Path("./logs")
LOG_FILE = LOG_DIR / "audit.jsonl"


class AuditLogger:
    """
    Lightweight structured logger for SmartDesk agent interactions.
    Each log entry is a self-contained JSON object with timing info.
    """

    def __init__(self, session_id: str = None):
        LOG_DIR.mkdir(exist_ok=True)

        self.session_id = session_id or f"session_{int(time.time())}"
        self._turn_start: float = 0
        self._current_input: str = ""

    def log_input(self, user_input: str):
        """Call this when the user sends a message."""
        self._turn_start = time.time()
        self._current_input = user_input

    def log_output(self, agent_response: str, tool_calls: list = None,
                   rag_scores: dict = None):
        """Call this when the agent finishes a turn."""
        entry = {
            "session_id":    self.session_id,
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "latency_ms":    round((time.time() - self._turn_start) * 1000),
            "input":         self._current_input,
            "output":        agent_response,
            "tool_calls":    tool_calls or [],
            "rag_scores":    rag_scores or {},
        }
        self._write(entry)

    def log_error(self, error: Exception, context: str = ""):
        """Log an error with context for debugging."""
        entry = {
            "session_id": self.session_id,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "level":      "ERROR",
            "error":      str(error),
            "context":    context,
        }
        self._write(entry)
        print(f"❌ Error logged: {error}")

    def _write(self, entry: dict):
        """Append a JSON entry to the log file."""
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def tail_logs(n: int = 10) -> list[dict]:
    """
    Read the last N log entries. Useful for debugging.
    Usage: from logging.audit_logger import tail_logs; print(tail_logs(5))
    """
    if not LOG_FILE.exists():
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return [json.loads(line) for line in lines[-n:] if line.strip()]
