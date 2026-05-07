from datetime import datetime, timezone, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES


def get_calendar_service():
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
    return build("calendar", "v3", credentials=creds)


def get_todays_events(service) -> list[dict]:
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return result.get("items", [])


def format_event(event: dict) -> str:
    summary = event.get("summary", "(No title)")
    start = event.get("start", {})
    time_str = start.get("dateTime", start.get("date", ""))
    if "T" in time_str:
        dt = datetime.fromisoformat(time_str)
        time_str = dt.strftime("%-I:%M %p")
    else:
        time_str = "All day"
    location = event.get("location", "")
    loc_part = f" @ {location}" if location else ""
    return f"  • {time_str}{loc_part} — {summary}"


def format_events_section(events: list[dict]) -> str:
    if not events:
        return "  • No events scheduled today — full focus day."
    return "\n".join(format_event(e) for e in events)
