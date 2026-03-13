"""
integrations/google_workspace.py — Google Sheets & Docs API
──────────────────────────────────────────────────────────────
WHAT THIS FILE DOES:
  - Append rows to a Google Sheet (e.g., log agent actions, inventory updates)
  - Read data from a Google Sheet (e.g., check stock levels)
  - Create a Google Doc from a text summary

SETUP (one-time):
  1. Go to https://console.cloud.google.com
  2. Create a project → enable "Google Sheets API" and "Google Docs API"
  3. Create a Service Account:
       IAM & Admin → Service Accounts → Create
  4. Download the JSON key file
  5. Set in .env:
       GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
  6. Share your Google Sheet with the service account email
     (it looks like: your-sa@your-project.iam.gserviceaccount.com)

INSTALL:
  pip install google-auth google-auth-httplib2 google-api-python-client
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()


def _get_credentials():
    """Build Google credentials from the service account JSON file."""
    try:
        from google.oauth2 import service_account

        sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        if not sa_path or not os.path.exists(sa_path):
            raise FileNotFoundError(
                f"Service account file not found: '{sa_path}'. "
                "Set GOOGLE_SERVICE_ACCOUNT_JSON in .env"
            )

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/documents",
        ]
        creds = service_account.Credentials.from_service_account_file(
            sa_path, scopes=scopes
        )
        return creds

    except ImportError:
        raise ImportError(
            "Google API client not installed. "
            "Run: pip install google-auth google-auth-httplib2 google-api-python-client"
        )


def append_to_sheet(spreadsheet_id: str, sheet_name: str, rows: list[list]) -> str:
    """
    Append one or more rows to a Google Sheet.

    Args:
        spreadsheet_id: The ID from the sheet URL
                        (https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit)
        sheet_name:     Tab name, e.g. "Sheet1" or "Agent Logs"
        rows:           List of rows, each row is a list of values
                        e.g. [["2024-01-15", "Query", "Answer", 0.94]]

    Returns:
        Human-readable success/failure string for the agent to relay.
    """
    try:
        from googleapiclient.discovery import build

        creds   = _get_credentials()
        service = build("sheets", "v4", credentials=creds)

        body = {"values": rows}
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="USER_ENTERED",  # parse dates and numbers
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()

        updated = result.get("updates", {}).get("updatedRows", 0)
        return f"✅ Appended {updated} row(s) to '{sheet_name}'"

    except Exception as e:
        return f"❌ Google Sheets error: {str(e)}"


def read_sheet(spreadsheet_id: str, range_notation: str) -> list[list]:
    """
    Read a range of cells from a Google Sheet.

    Args:
        spreadsheet_id:  Sheet ID from the URL
        range_notation:  A1 notation, e.g. "Sheet1!A1:D50"

    Returns:
        List of rows (each row is a list of cell values as strings).
    """
    try:
        from googleapiclient.discovery import build

        creds   = _get_credentials()
        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
        ).execute()

        return result.get("values", [])

    except Exception as e:
        print(f"❌ Google Sheets read error: {e}")
        return []


def create_google_doc(title: str, content: str) -> str:
    """
    Create a new Google Doc with the given title and plain text content.

    Returns the URL of the newly created document.
    """
    try:
        from googleapiclient.discovery import build

        creds       = _get_credentials()
        docs_svc    = build("docs", "v1", credentials=creds)
        drive_svc   = build("drive", "v3", credentials=creds)

        # Step 1: Create an empty doc
        doc = docs_svc.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]

        # Step 2: Insert the content
        requests = [{
            "insertText": {
                "location": {"index": 1},
                "text": content,
            }
        }]
        docs_svc.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests},
        ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return f"✅ Google Doc created: {doc_url}"

    except Exception as e:
        return f"❌ Google Docs error: {str(e)}"
