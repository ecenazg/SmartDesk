"""
agent/tools.py — SmartDesk Agent Tools
───────────────────────────────────────
WHAT THIS FILE DOES:
  Defines the tools the LangChain agent can call.
  Think of tools as the agent's "hands" — it reads the tool descriptions
  and decides which one to use based on the user's intent.

HOW LANGCHAIN TOOL ROUTING WORKS:
  The agent sees each tool's name + description in its prompt.
  GPT-4o then picks the right tool (or combination) and formats
  the arguments. LangChain executes the tool and feeds the result
  back into the agent's reasoning loop.

TOOLS DEFINED HERE:
  1. search_knowledge_base  — RAG retrieval from your documents
  2. trigger_workflow        — fires a webhook to n8n or Make.com
  3. send_slack_notification — posts a Slack message
  4. create_clickup_task     — creates a task in ClickUp
"""

import os
import requests
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()


# ── Workflow Registry ─────────────────────────────────────────────────────────
# Maps friendly workflow names → webhook URLs from .env
# Add new workflows here as you build them in n8n/Make.com

WORKFLOW_REGISTRY = {
    "create_task":            os.getenv("N8N_WEBHOOK_URL", ""),
    "send_slack_notification": os.getenv("SLACK_WEBHOOK_URL", ""),
    "log_to_sheet":           os.getenv("MAKE_WEBHOOK_URL", ""),
    "update_inventory":       os.getenv("N8N_WEBHOOK_URL", ""),
}


# ── Tool 1: Knowledge Base Search ────────────────────────────────────────────

# Note: We can't pass the chain directly into @tool decorator easily,
# so we use a module-level variable set at startup by main.py

_rag_chain = None

def set_rag_chain(chain):
    """Called once at startup to inject the RAG chain into this module."""
    global _rag_chain
    _rag_chain = chain


@tool
def search_knowledge_base(question: str) -> str:
    """
    Search the internal knowledge base to answer questions about company
    policies, processes, SOPs, FAQs, and procedures.
    Use this tool whenever the user asks a factual question about
    internal documentation, workflows, or business processes.
    """
    if _rag_chain is None:
        return "Knowledge base is not initialized. Run ingest.py first."

    from rag.retriever import query_knowledge_base
    from rag.evaluator import evaluate_rag_response

    result = query_knowledge_base(_rag_chain, question)
    answer = result["answer"]
    contexts = result["contexts"]

    # Evaluate quality inline (light-weight — only faithfulness + relevancy)
    scores = evaluate_rag_response(question, answer, contexts)

    score_line = ""
    if scores["faithfulness"] is not None:
        score_line = (f"\n[Faithfulness: {scores['faithfulness']} | "
                      f"Relevance: {scores['answer_relevancy']}]")

    return f"{answer}{score_line}"


# ── Tool 2: Workflow Automation ───────────────────────────────────────────────

@tool
def trigger_workflow(workflow_name: str, payload: str) -> str:
    """
    Trigger an automated workflow via webhook. Use this when the user
    wants to CREATE a task, LOG data, UPDATE a spreadsheet,
    or SEND a notification through an automated process.

    workflow_name options: create_task, send_slack_notification,
                           log_to_sheet, update_inventory
    payload: a plain-English description of what to include
             (the tool will format it as JSON automatically)
    """
    if workflow_name not in WORKFLOW_REGISTRY:
        return (f"Unknown workflow '{workflow_name}'. "
                f"Available: {list(WORKFLOW_REGISTRY.keys())}")

    webhook_url = WORKFLOW_REGISTRY[workflow_name]

    if not webhook_url:
        return (f"Webhook URL for '{workflow_name}' is not configured. "
                f"Add it to your .env file.")

    try:
        response = requests.post(
            webhook_url,
            json={"workflow": workflow_name, "payload": payload},
            timeout=10,
        )
        return (f"✅ Workflow '{workflow_name}' triggered successfully. "
                f"Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        return f"❌ Workflow trigger failed: {str(e)}"


# ── Tool 3: Direct Slack Notification ────────────────────────────────────────

@tool
def send_slack_message(message: str) -> str:
    """
    Send a direct message to the configured Slack channel.
    Use this for quick notifications, alerts, or status updates.
    """
    slack_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not slack_url:
        return "SLACK_WEBHOOK_URL is not set in .env"

    try:
        response = requests.post(slack_url, json={"text": message}, timeout=10)
        if response.status_code == 200:
            return f"✅ Slack message sent: '{message[:60]}...'"
        return f"❌ Slack error: {response.status_code} — {response.text}"
    except requests.exceptions.RequestException as e:
        return f"❌ Slack request failed: {str(e)}"


# ── Tool 4: ClickUp Task Creation ────────────────────────────────────────────

@tool
def create_clickup_task(task_name: str, description: str, due_date: str = "") -> str:
    """
    Create a task in ClickUp. Use this when the user explicitly asks to
    create a task, add a to-do item, or schedule a follow-up action.

    task_name:   Short title for the task
    description: What needs to be done
    due_date:    Optional due date in plain English (e.g., "next Monday")
    """
    from integrations.clickup import create_task
    return create_task(task_name, description, due_date)


# ── Tool Registry ─────────────────────────────────────────────────────────────
# This list is passed to the LangChain agent at startup.

ALL_TOOLS = [
    search_knowledge_base,
    trigger_workflow,
    send_slack_message,
    create_clickup_task,
]
