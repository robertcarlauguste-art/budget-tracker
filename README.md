# Rovana Studio — AI Agent Team

An automated production pipeline for Robert Auguste / Rovana Studio.
Two AI agents run on a cron schedule, taking you from morning research to production-ready creative briefs — all landing in Gmail Drafts for review.

## The Team

| Agent | Role | Schedule |
|-------|------|----------|
| **Kevin** | Chief of Staff | 9:00 AM, 2:00 PM, every 30 min |
| **Sam** | Creative Director | 9:30 AM |

## Daily Pipeline

```
9:00 AM  Kevin  → Morning briefing (research + calendar + email triage) → Gmail Draft
9:30 AM  Sam    → Picks best 2 ideas → writes detailed creative briefs  → Gmail Draft
         ↓
         Robert reviews Sam's briefs ← HUMAN CHECKPOINT
         ↓
manual   Alex   → Engineers 3 Imagen prompts per concept → Gmail Draft
manual   Imagen → Generates images via Google Imagen 3 → workspace/generated/
         ↓
         Robert reviews images ← HUMAN CHECKPOINT
         ↓
[coming] Production Prep Agent → POD-ready files (resize, DPI, bleed)
[coming] Listing Agent → Etsy listing copy + SEO tags
```

## What Kevin Delivers (9 AM)
1. **Top 3 Priorities** for the day
2. **Calendar** — today's events from Google Calendar
3. **5 Design Ideas** — researched live from trending POD/digital niches
4. **Trending Memes & Slogans** — current viral content to repurpose for the shop
5. **Emails Needing Reply** — with drafted replies in Robert's voice

## What Sam Delivers (9:30 AM)
From Kevin's 5 ideas + memes, Sam picks the **2 strongest** and writes a detailed creative brief for each:
- Target audience, product types, style direction (colors, mood, typography)
- Design direction for the designer
- Ready-to-use image generation prompt
- Why this will sell, why the timing is right

## What Alex Delivers (manual — after reviewing Sam's briefs)
Alex takes Sam's brief and engineers **3 production-ready Imagen 3 prompts** per concept:
- Safe/clean variant, bold/experimental variant, minimal variant
- Correct aspect ratios per product type (1:1 for POD, 3:4 for art prints)
- Negative prompts to steer clear of common AI image failures

## What Imagen Delivers (manual — after reviewing Alex's specs)
Calls Google Imagen 3 API and saves generated images to `workspace/generated/YYYYMMDD/`.
A summary draft lands in Gmail Drafts with file paths for review.

---

## Setup (Do This Once)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API keys

```bash
cp .env.example .env
# Edit .env and add:
#   ANTHROPIC_API_KEY=sk-ant-...       (from console.anthropic.com)
#   GOOGLE_AI_API_KEY=...              (from aistudio.google.com/app/apikey)
```

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

# Kevin
python chief_of_staff/main.py briefing          # Generate morning briefing
python chief_of_staff/main.py email-check       # Afternoon email check
python chief_of_staff/main.py urgent-check      # Urgent email scan

# Sam
python chief_of_staff/main.py creative-brief    # Creative briefs from today's research

# Alex (run after reviewing Sam's brief)
python chief_of_staff/main.py design-spec       # Image generation specs

# Imagen (run after reviewing Alex's specs)
python chief_of_staff/main.py generate-images   # Generate images via Google Imagen 3
```

---

## Files

```
chief_of_staff/
├── main.py              # CLI entry point — all agents dispatched from here
├── config.py            # Business settings, voice profile, constants
├── gmail_client.py      # Gmail API wrapper
├── calendar_client.py   # Google Calendar API wrapper
├── research.py          # Kevin: web search via Claude (design ideas, memes)
├── email_monitor.py     # Kevin: email classification and reply drafting
├── briefing.py          # Kevin: morning briefing assembler
├── sam.py               # Sam: creative director briefs
├── alex.py              # Alex: image generation specs
├── imagen_client.py     # Agent 4: Google Imagen 3 image generation
├── setup_oauth.py       # One-time OAuth setup
└── credentials/         # Your credentials (gitignored — never committed)
workspace/               # Shared state between agents
  ├── research_YYYYMMDD.json      # Kevin's research output
  ├── creative_brief_YYYYMMDD.json # Sam's briefs
  ├── design_specs_YYYYMMDD.json  # Alex's specs
  └── generated/YYYYMMDD/         # Generated images
requirements.txt
crontab.txt
.env.example
```

---

## Security

- `chief_of_staff/credentials/` is gitignored — your OAuth tokens never leave this machine
- `.env` is gitignored — your API key stays local
- Kevin only reads email and creates drafts — it never sends anything without your review
