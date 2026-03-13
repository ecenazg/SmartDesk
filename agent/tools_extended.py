"""
agent/tools_extended.py — Additional Agent Tools
─────────────────────────────────────────────────
Extra tools that connect to Google Workspace.
These are kept separate so the core tools.py stays clean.

To activate: import ALL_TOOLS_EXTENDED and add to the agent in agent.py.
"""

from langchain.tools import tool


@tool
def log_interaction_to_sheet(summary: str) -> str:
    """
    Log an important interaction or decision to the team's Google Sheet.
    Use this when the user wants to record something for audit or reporting.
    Example: "Log that we approved the $800 return exception today"

    summary: Plain English description of what happened
    """
    import os
    from datetime import datetime
    from integrations.google_workspace import append_to_sheet

    spreadsheet_id = os.getenv("GOOGLE_SHEET_ID", "")
    if not spreadsheet_id:
        return "❌ GOOGLE_SHEET_ID is not set in .env"

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        summary,
        "SmartDesk Agent",
    ]
    return append_to_sheet(spreadsheet_id, "Agent Logs", [row])


@tool
def create_summary_doc(title: str, content: str) -> str:
    """
    Create a Google Doc with a summary or report.
    Use this when the user wants to save a document for the team,
    generate a meeting summary, or produce a process writeup.

    title:   Document title
    content: The full text content to put in the document
    """
    from integrations.google_workspace import create_google_doc
    return create_google_doc(title, content)


ALL_TOOLS_EXTENDED = [
    log_interaction_to_sheet,
    create_summary_doc,
]
