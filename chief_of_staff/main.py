#!/usr/bin/env python3
"""Rovana Studio — AI Agent Team.

Usage:
  python main.py briefing        # Kevin: morning briefing draft → Gmail Drafts (9 AM)
  python main.py email-check     # Kevin: afternoon email check + reply drafts (2 PM)
  python main.py urgent-check    # Kevin: scan for urgent emails (every 30 min)
  python main.py creative-brief  # Sam: creative director briefs from today's research (9:30 AM)
"""

import sys
import os
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import anthropic

from gmail_client import get_gmail_service
from calendar_client import get_calendar_service
from email_monitor import process_urgent_check, process_email_check, save_reply_drafts, format_email_section
from briefing import generate_briefing
from sam import generate_creative_briefs
from config import CREDENTIALS_FILE, TOKEN_FILE


def check_prerequisites():
    if not CREDENTIALS_FILE.exists():
        print("ERROR: Google credentials not found.")
        print(f"  Expected: {CREDENTIALS_FILE}")
        print("  Run: python setup_oauth.py")
        sys.exit(1)
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)


def cmd_briefing():
    print("[Kevin] Generating morning briefing...")
    check_prerequisites()
    gmail = get_gmail_service()
    cal = get_calendar_service()
    generate_briefing(gmail, cal)
    print("[Kevin] Done. Check your Gmail Drafts folder.")


def cmd_email_check():
    print("[Kevin] Running afternoon email check...")
    check_prerequisites()
    client = anthropic.Anthropic()
    gmail = get_gmail_service()
    results = process_email_check(client, gmail, hours_ago=12)
    count = save_reply_drafts(gmail, results, urgent_prefix=False)
    if count:
        print(f"[Kevin] {count} reply draft(s) saved to Gmail Drafts.")
        print(format_email_section(results))
    else:
        print("[Kevin] Inbox clear — no replies needed.")


def cmd_urgent_check():
    check_prerequisites()
    client = anthropic.Anthropic()
    gmail = get_gmail_service()
    results = process_urgent_check(client, gmail)
    if results:
        count = save_reply_drafts(gmail, results, urgent_prefix=True)
        print(f"[Kevin] URGENT: {count} urgent email(s) flagged. Check Gmail Drafts now.")
        for r in results:
            print(f"  • {r['sender']} — {r['subject']}")
    # Silent if nothing urgent (runs every 30 min, no noise needed)


def cmd_creative_brief():
    print("[Sam] Generating creative briefs from today's research...")
    check_prerequisites()
    gmail = get_gmail_service()
    briefs = generate_creative_briefs(gmail_service=gmail)
    if briefs:
        print(f"[Sam] Done. {len(briefs)} brief(s) drafted — check Gmail Drafts.")
        for b in briefs:
            print(f"  • {b['concept_name']}: {b['one_liner']}")
    else:
        print("[Sam] No briefs generated. Check that Kevin's briefing ran first.")


COMMANDS = {
    "briefing": cmd_briefing,
    "email-check": cmd_email_check,
    "urgent-check": cmd_urgent_check,
    "creative-brief": cmd_creative_brief,
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
