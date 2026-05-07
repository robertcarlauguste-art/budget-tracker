import base64
import email as email_lib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, BUSINESS_EMAIL


def get_gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def search_threads(service, query: str, max_results: int = 20) -> list[dict]:
    result = service.users().threads().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    return result.get("threads", [])


def get_thread_messages(service, thread_id: str) -> list[dict]:
    thread = service.users().threads().get(
        userId="me", threadId=thread_id, format="full"
    ).execute()
    return thread.get("messages", [])


def extract_message_body(message: dict) -> str:
    payload = message.get("payload", {})
    parts = payload.get("parts", [])

    def decode_part(part):
        data = part.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return ""

    if parts:
        for part in parts:
            if part.get("mimeType") == "text/plain":
                return decode_part(part)
        for part in parts:
            if part.get("mimeType") == "text/html":
                return decode_part(part)
    return decode_part(payload)


def get_message_headers(message: dict) -> dict:
    headers = message.get("payload", {}).get("headers", [])
    return {h["name"].lower(): h["value"] for h in headers}


def get_unread_threads_since(service, hours_ago: int) -> list[dict]:
    since_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours_ago)).timestamp())
    query = f"is:unread after:{since_ts}"
    return search_threads(service, query)


def get_unanswered_threads(service, hours_ago: int = 24) -> list[dict]:
    since_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours_ago)).timestamp())
    query = f"is:unread -from:me after:{since_ts} category:primary"
    return search_threads(service, query)


def create_draft(service, to: str, subject: str, body: str) -> dict:
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["from"] = BUSINESS_EMAIL
    message["subject"] = subject
    message.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()
    return draft


def create_reply_draft(service, thread_id: str, to: str, subject: str, body: str) -> dict:
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["from"] = BUSINESS_EMAIL
    message["subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    message.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw, "threadId": thread_id}},
    ).execute()
    return draft
