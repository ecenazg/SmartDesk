"""
tests/test_core.py — SmartDesk Unit Tests
────────────────────────────────────────────
Tests for the core components that don't require an OpenAI API key.

RUN:
  pip install pytest
  pytest tests/ -v

These tests use mocking so they run fast and free — no API calls.
"""

import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Audit Logger Tests ────────────────────────────────────────────────────────

class TestAuditLogger:
    def test_creates_log_file(self, tmp_path, monkeypatch):
        """Logger should create the log file on first write."""
        import logging.audit_logger as al
        monkeypatch.setattr(al, "LOG_DIR", tmp_path)
        monkeypatch.setattr(al, "LOG_FILE", tmp_path / "test_audit.jsonl")

        from logging.audit_logger import AuditLogger
        logger = AuditLogger(session_id="test_session")
        logger.log_input("Hello")
        logger.log_output("World")

        log_file = tmp_path / "test_audit.jsonl"
        assert log_file.exists()

    def test_log_entry_structure(self, tmp_path, monkeypatch):
        """Each log entry should contain required fields."""
        import logging.audit_logger as al
        monkeypatch.setattr(al, "LOG_DIR", tmp_path)
        monkeypatch.setattr(al, "LOG_FILE", tmp_path / "test_audit.jsonl")

        from logging.audit_logger import AuditLogger
        logger = AuditLogger(session_id="test_123")
        logger.log_input("test question")
        logger.log_output("test answer")

        log_file = tmp_path / "test_audit.jsonl"
        entry = json.loads(log_file.read_text().strip())

        assert entry["session_id"] == "test_123"
        assert entry["input"] == "test question"
        assert entry["output"] == "test answer"
        assert "timestamp" in entry
        assert "latency_ms" in entry


# ── Webhook Tests ─────────────────────────────────────────────────────────────

class TestWebhook:
    @patch("integrations.webhook.requests.post")
    def test_successful_webhook_call(self, mock_post):
        """Webhook should return success on 200 response."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        from integrations.webhook import call_webhook
        result = call_webhook("https://example.com/webhook", {"key": "value"})

        assert result["success"] is True
        assert result["status_code"] == 200
        mock_post.assert_called_once()

    @patch("integrations.webhook.requests.post")
    def test_failed_webhook_call(self, mock_post):
        """Webhook should return failure on non-2xx response."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_post.return_value = mock_response

        from integrations.webhook import call_webhook
        result = call_webhook("https://example.com/webhook", {})

        assert result["success"] is False

    @patch("integrations.webhook.requests.post")
    def test_missing_env_returns_error(self, mock_post, monkeypatch):
        """trigger_n8n should fail gracefully when URL is not set."""
        monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)

        from integrations.webhook import trigger_n8n
        result = trigger_n8n("test_workflow", {"data": "test"})

        assert result["success"] is False
        assert "not set" in result["error"]
        mock_post.assert_not_called()


# ── RAG Evaluator Tests ───────────────────────────────────────────────────────

class TestRAGEvaluator:
    @patch("rag.evaluator.evaluate")
    def test_evaluate_returns_scores(self, mock_evaluate):
        """evaluate_rag_response should return a dict with score keys."""
        mock_result = MagicMock()
        mock_result.__getitem__ = lambda self, key: 0.95 if key == "faithfulness" else 0.91
        mock_evaluate.return_value = mock_result

        from rag.evaluator import evaluate_rag_response
        scores = evaluate_rag_response(
            question="Test question?",
            answer="Test answer.",
            contexts=["Context chunk 1", "Context chunk 2"],
        )

        assert "faithfulness" in scores
        assert "answer_relevancy" in scores

    def test_evaluate_handles_import_error_gracefully(self):
        """Evaluator should not crash if RAGAS is misconfigured."""
        from rag.evaluator import evaluate_rag_response

        with patch("builtins.__import__", side_effect=ImportError("ragas not found")):
            # Should return None scores, not raise
            scores = evaluate_rag_response("q", "a", ["ctx"])
            # Either None scores or a dict — either is acceptable failure handling
            assert isinstance(scores, dict)


# ── Tool Registry Tests ───────────────────────────────────────────────────────

class TestToolRegistry:
    def test_all_tools_are_callable(self):
        """Every tool in ALL_TOOLS should be a valid LangChain tool."""
        from agent.tools import ALL_TOOLS
        from langchain.tools import BaseTool

        for tool in ALL_TOOLS:
            assert hasattr(tool, "name"), f"{tool} missing .name"
            assert hasattr(tool, "description"), f"{tool} missing .description"
            assert callable(tool.func) or callable(tool._run), \
                f"{tool.name} is not callable"

    def test_tool_names_are_unique(self):
        """Tool names must be unique — duplicate names break the agent."""
        from agent.tools import ALL_TOOLS
        names = [t.name for t in ALL_TOOLS]
        assert len(names) == len(set(names)), f"Duplicate tool names: {names}"