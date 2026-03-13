"""
integrations/webhook.py — Generic Webhook Caller
──────────────────────────────────────────────────
Handles all outgoing HTTP calls to n8n and Make.com.
Both platforms accept standard POST requests with JSON payloads —
this single file works for both without any changes.

HOW TO SET UP n8n:
  1. Create a workflow in n8n
  2. Add a "Webhook" trigger node as the first step
  3. Copy the webhook URL → paste into .env as N8N_WEBHOOK_URL
  4. Connect output nodes (e.g., ClickUp, Google Sheets, Slack)

HOW TO SET UP Make.com:
  1. Create a scenario in Make.com
  2. Add a "Webhooks > Custom Webhook" module as the trigger
  3. Copy the webhook URL → paste into .env as MAKE_WEBHOOK_URL
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TIMEOUT = 10  # seconds


def call_webhook(url: str, payload: dict, retries: int = 2) -> dict:
    """
    POST a JSON payload to a webhook URL with basic retry logic.

    Args:
        url:     Webhook URL (from n8n or Make.com)
        payload: Data to send (will be JSON-serialized)
        retries: Number of retry attempts on failure

    Returns:
        dict with 'success', 'status_code', and 'response' keys
    """
    for attempt in range(retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            return {
                "success":     response.ok,
                "status_code": response.status_code,
                "response":    response.text[:500],  # truncate long responses
            }
        except requests.exceptions.Timeout:
            if attempt == retries:
                return {"success": False, "error": "Webhook timed out"}
        except requests.exceptions.RequestException as e:
            if attempt == retries:
                return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded"}


def trigger_n8n(workflow_name: str, data: dict) -> dict:
    """Trigger an n8n workflow by name."""
    url = os.getenv("N8N_WEBHOOK_URL", "")
    if not url:
        return {"success": False, "error": "N8N_WEBHOOK_URL not set in .env"}

    payload = {"workflow": workflow_name, "data": data}
    return call_webhook(url, payload)


def trigger_make(scenario_name: str, data: dict) -> dict:
    """Trigger a Make.com scenario."""
    url = os.getenv("MAKE_WEBHOOK_URL", "")
    if not url:
        return {"success": False, "error": "MAKE_WEBHOOK_URL not set in .env"}

    payload = {"scenario": scenario_name, "data": data}
    return call_webhook(url, payload)
