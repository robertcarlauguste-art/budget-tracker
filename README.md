# Kevin — AI Chief of Staff for Rovana Studio

Kevin is an automated Chief of Staff for Robert Auguste / Rovana Studio. Every morning at 9 AM, Kevin drops a briefing into your Gmail Drafts with design ideas, trending content, your calendar, and drafted email replies — all researched in real time.

## What Kevin Does

| Schedule | Task |
|----------|------|
| 9:00 AM daily | Morning briefing draft → Gmail Drafts |
| 2:00 PM daily | Afternoon email check → drafts replies |
| Every 30 min | Scans for urgent emails → flags in Drafts |

The morning briefing includes:
1. **Top 3 Priorities** for the day
2. **Calendar** — today's events from Google Calendar
3. **5 Design Ideas** — researched live from trending POD/digital niches
4. **Trending Memes & Slogans** — current viral content to repurpose for the shop
5. **Emails Needing Reply** — with drafted replies in Robert's voice, ready to review and send

---

## Setup (Do This Once)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key

```bash
cp .env.example .env
# Edit .env and add your key: ANTHROPIC_API_KEY=sk-ant-...
```

Get your API key at [console.anthropic.com](https://console.anthropic.com/).

### 3. Set up Google API access

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project
3. Enable **Gmail API** and **Google Calendar API**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Choose **Desktop app**, download the JSON
6. Save it as: `chief_of_staff/credentials/credentials.json`

### 4. Authorize Kevin (browser login — one time only)

```bash
cd chief_of_staff
python setup_oauth.py
```

Log in with **rovanastudio@gmail.com** when the browser opens. Token is saved locally.

### 5. Install the cron schedule

```bash
crontab -e
# Paste the contents of crontab.txt
```

---

## Manual Usage

```bash
cd /home/user/budget-tracker

# Generate today's briefing now
python chief_of_staff/main.py briefing

# Run afternoon email check
python chief_of_staff/main.py email-check

# Check for urgent emails right now
python chief_of_staff/main.py urgent-check
```

---

## Files

```
chief_of_staff/
├── main.py              # CLI entry point
├── config.py            # Business settings, voice profile, constants
├── gmail_client.py      # Gmail API wrapper
├── calendar_client.py   # Google Calendar API wrapper
├── research.py          # Web search via Claude (design ideas, memes)
├── email_monitor.py     # Email classification and reply drafting
├── briefing.py          # Morning briefing assembler
├── setup_oauth.py       # One-time OAuth setup
└── credentials/         # Your credentials (gitignored — never committed)
requirements.txt
crontab.txt
.env.example
```

---

## Security

- `chief_of_staff/credentials/` is gitignored — your OAuth tokens never leave this machine
- `.env` is gitignored — your API key stays local
- Kevin only reads email and creates drafts — it never sends anything without your review
