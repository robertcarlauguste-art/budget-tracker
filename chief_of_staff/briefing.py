import json
from datetime import datetime
from pathlib import Path

import anthropic

from config import (
    CLAUDE_MODEL,
    BUSINESS_EMAIL,
    OWNER_NAME,
    BUSINESS_NAME,
    TOP_3_PRIORITIES,
)
from calendar_client import get_todays_events, format_events_section
from research import get_design_ideas, get_trending_memes
from email_monitor import process_email_check, save_reply_drafts, format_email_section
from gmail_client import create_draft

WORKSPACE_DIR = Path(__file__).parent.parent / "workspace"


BRIEFING_TEMPLATE = """\
Good morning, {owner},

Here's your daily brief from Kevin — {date}.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOP 3 PRIORITIES TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{priorities}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CALENDAR TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{calendar}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 DESIGN IDEAS — DIGITAL & PRINT ON DEMAND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{design_ideas}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRENDING MEMES & SLOGANS TO REPURPOSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{memes}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EMAILS NEEDING YOUR REPLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{emails}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
— Kevin, your Chief of Staff
{business} | {email}
"""


def generate_briefing(gmail_service, calendar_service) -> str:
    client = anthropic.Anthropic()
    today = datetime.now()
    date_str = today.strftime("%A, %B %-d, %Y")

    print("  [Kevin] Checking calendar...")
    events = get_todays_events(calendar_service)
    calendar_section = format_events_section(events)

    print("  [Kevin] Researching design ideas (web search)...")
    design_ideas = get_design_ideas(client)

    print("  [Kevin] Researching trending memes (web search)...")
    memes = get_trending_memes(client)

    print("  [Kevin] Checking email inbox...")
    email_results = process_email_check(client, gmail_service, hours_ago=24)

    print(f"  [Kevin] Drafting replies for {len(email_results)} email(s)...")
    save_reply_drafts(gmail_service, email_results, urgent_prefix=False)
    email_section = format_email_section(email_results)

    priorities_text = "\n".join(f"  {i}. {p}" for i, p in enumerate(TOP_3_PRIORITIES, 1))

    body = BRIEFING_TEMPLATE.format(
        owner=OWNER_NAME,
        date=date_str,
        priorities=priorities_text,
        calendar=calendar_section,
        design_ideas=design_ideas,
        memes=memes,
        emails=email_section,
        business=BUSINESS_NAME,
        email=BUSINESS_EMAIL,
    )

    # Save research to workspace so Sam can pick it up
    WORKSPACE_DIR.mkdir(exist_ok=True)
    research_file = WORKSPACE_DIR / f"research_{today.strftime('%Y%m%d')}.json"
    research_file.write_text(json.dumps({
        "date": today.isoformat(),
        "design_ideas": design_ideas,
        "memes": memes,
    }, indent=2))
    print(f"  [Kevin] Research saved to workspace for Sam.")

    subject = f"Kevin's Brief — {today.strftime('%A %B %-d')}"
    draft = create_draft(gmail_service, to=BUSINESS_EMAIL, subject=subject, body=body)
    print(f"  [Kevin] Briefing draft created: {draft.get('id', 'unknown')}")
    return body
