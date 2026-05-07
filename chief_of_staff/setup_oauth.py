#!/usr/bin/env python3
"""One-time OAuth setup. Run this once to authorize Kevin to access your Gmail and Calendar.

Usage:
  python setup_oauth.py

This will open a browser window asking you to log in with rovanastudio@gmail.com
and grant permission. The token is saved locally and reused automatically.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from google_auth_oauthlib.flow import InstalledAppFlow
from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, BUSINESS_EMAIL


def main():
    if not CREDENTIALS_FILE.exists():
        print("ERROR: credentials.json not found.")
        print(f"  Expected at: {CREDENTIALS_FILE}")
        print()
        print("To get credentials.json:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a project (or use an existing one)")
        print("  3. Enable the Gmail API and Google Calendar API")
        print("  4. Go to APIs & Services > Credentials")
        print("  5. Create OAuth 2.0 Client ID (Desktop app)")
        print("  6. Download the JSON and save it as:")
        print(f"     {CREDENTIALS_FILE}")
        sys.exit(1)

    print(f"Opening browser to authorize Kevin for: {BUSINESS_EMAIL}")
    print("Make sure to log in with your BUSINESS account (rovanastudio@gmail.com).\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(creds.to_json())
    print(f"\nAuthorization complete. Token saved to: {TOKEN_FILE}")
    print("\nKevin is now authorized. Run a test:")
    print("  python main.py briefing")


if __name__ == "__main__":
    main()
