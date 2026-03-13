"""
integrations/clickup.py — ClickUp Task Creation
────────────────────────────────────────────────
Creates tasks via the ClickUp REST API.

SETUP:
  1. Go to ClickUp → Settings → Apps → API Token
  2. Copy your token → paste into .env as CLICKUP_API_TOKEN
  3. Find your List ID: open a list in ClickUp, the URL contains it
     e.g. https://app.clickup.com/123/v/l/li/LIST_ID_HERE
  4. Set CLICKUP_LIST_ID in .env
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


def create_task(task_name: str, description: str, due_date: str = "") -> str:
    """
    Create a ClickUp task via REST API.

    Returns a human-readable success/failure string for the agent to relay.
    """
    api_token = os.getenv("CLICKUP_API_TOKEN", "")
    list_id   = os.getenv("CLICKUP_LIST_ID", "")

    if not api_token:
        return "❌ CLICKUP_API_TOKEN is not set in .env"
    if not list_id:
        return "❌ CLICKUP_LIST_ID is not set in .env"

    headers = {
        "Authorization": api_token,
        "Content-Type":  "application/json",
    }

    payload = {
        "name":        task_name,
        "description": description,
        "status":      "Open",
    }

    # ClickUp expects due_date as a Unix timestamp in milliseconds
    if due_date:
        payload["due_date_time"] = True
        # Simple date parsing — in production, use dateparser library
        payload["due_date"] = _parse_due_date(due_date)

    try:
        response = requests.post(
            f"{CLICKUP_API_BASE}/list/{list_id}/task",
            headers=headers,
            json=payload,
            timeout=10,
        )

        if response.ok:
            task = response.json()
            task_url = task.get("url", "")
            return f"✅ Task created: '{task_name}' | URL: {task_url}"
        else:
            return f"❌ ClickUp error {response.status_code}: {response.text[:200]}"

    except requests.exceptions.RequestException as e:
        return f"❌ ClickUp request failed: {str(e)}"


def _parse_due_date(due_date_str: str) -> int:
    """
    Convert a plain English date to Unix timestamp in milliseconds.
    Install dateparser for better coverage: pip install dateparser
    """
    try:
        import dateparser
        dt = dateparser.parse(due_date_str)
        if dt:
            import time
            return int(dt.timestamp() * 1000)
    except ImportError:
        pass

    # Fallback: return None (no due date)
    return None
