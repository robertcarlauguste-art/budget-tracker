"""Sam — Creative Director for Rovana Studio.

Sam takes Kevin's morning research and makes the creative call:
which ideas to pursue today, and how. She outputs a detailed creative brief
for each selected concept — ready for image generation.
"""

import json
from datetime import datetime
from pathlib import Path

import anthropic

from config import CLAUDE_MODEL, BUSINESS_NAME, BUSINESS_EMAIL, DELIVERY_EMAIL, OWNER_NAME
from gmail_client import create_draft

WORKSPACE_DIR = Path(__file__).parent.parent / "workspace"

SAM_SYSTEM = f"""You are Sam, Creative Director for {BUSINESS_NAME}, an Etsy shop
selling digital downloads and print-on-demand products.

Your job: take raw trend research and make sharp, decisive creative calls.
You pick the 2 strongest ideas from the daily research and write a detailed
creative brief for each one — specific enough that a designer (or AI image
generator) can execute it immediately.

Your personality:
- Decisive. You pick and commit. No hedging.
- Market-aware. You think about what sells, not just what looks good.
- Specific. Vague direction wastes time. You give exact colors, moods, references.
- Brief. Your briefs are tight. No filler.

You always write your briefs in this exact JSON structure so downstream agents
can parse and act on them programmatically."""


BRIEF_SCHEMA = """
Return a JSON array of exactly 2 creative briefs. Each brief must follow this schema:

[
  {
    "concept_name": "Short punchy name for this design concept",
    "one_liner": "One sentence pitch — why this will sell",
    "target_audience": "Who buys this. Be specific (e.g. 'millennial women who love true crime')",
    "product_types": ["list", "of", "specific", "product", "types"],
    "style": {
      "mood": "2-3 words describing the overall feel",
      "colors": ["hex or descriptive color names", "2-4 colors max"],
      "typography": "Font style direction (e.g. 'bold sans-serif, all caps')",
      "visual_references": "Real-world references (e.g. 'like a vintage 70s concert poster')"
    },
    "design_direction": "2-3 sentences of specific visual direction for the designer",
    "image_gen_prompt": "Ready-to-use prompt for DALL-E or Midjourney",
    "why_now": "One sentence on why this timing is right",
    "source": "which of Kevin's ideas or memes this came from"
  }
]

Return only valid JSON. No explanation before or after."""


def load_todays_research() -> dict | None:
    today = datetime.now().strftime("%Y%m%d")
    research_file = WORKSPACE_DIR / f"research_{today}.json"
    if research_file.exists():
        return json.loads(research_file.read_text())
    # Fall back to most recent research file
    files = sorted(WORKSPACE_DIR.glob("research_*.json"), reverse=True)
    if files:
        print(f"  [Sam] No research for today — using most recent: {files[0].name}")
        return json.loads(files[0].read_text())
    return None


def save_briefs(briefs: list[dict], date_str: str) -> Path:
    WORKSPACE_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    brief_file = WORKSPACE_DIR / f"creative_brief_{today}.json"
    brief_file.write_text(json.dumps(briefs, indent=2))
    return brief_file


def format_brief_for_email(brief: dict, index: int) -> str:
    style = brief.get("style", {})
    products = ", ".join(brief.get("product_types", []))
    colors = ", ".join(style.get("colors", []))
    return f"""
BRIEF {index}: {brief['concept_name'].upper()}
{brief['one_liner']}

Target: {brief['target_audience']}
Products: {products}
Why now: {brief['why_now']}

STYLE DIRECTION
  Mood: {style.get('mood', '')}
  Colors: {colors}
  Typography: {style.get('typography', '')}
  References: {style.get('visual_references', '')}

DESIGN DIRECTION
{brief['design_direction']}

IMAGE GEN PROMPT
"{brief['image_gen_prompt']}"

Source: {brief.get('source', 'Kevin research')}
""".strip()


def generate_creative_briefs(gmail_service=None) -> list[dict]:
    client = anthropic.Anthropic()
    today = datetime.now()
    date_str = today.strftime("%A, %B %-d, %Y")

    print("  [Sam] Loading Kevin's research...")
    research = load_todays_research()
    if not research:
        print("  [Sam] No research found. Run `python main.py briefing` first.")
        return []

    user_prompt = f"""Here is today's trend research from Kevin ({date_str}):

DESIGN IDEAS:
{research['design_ideas']}

TRENDING MEMES & SLOGANS:
{research['memes']}

Pick the 2 strongest opportunities for {BUSINESS_NAME} to create today.
Consider: sellability, timing, production feasibility for a solo operator.

{BRIEF_SCHEMA}"""

    print("  [Sam] Analyzing research and writing creative briefs...")
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SAM_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    briefs = json.loads(raw)

    brief_file = save_briefs(briefs, date_str)
    print(f"  [Sam] Briefs saved: {brief_file}")

    if gmail_service:
        _draft_brief_email(gmail_service, briefs, date_str)

    return briefs


def _draft_brief_email(gmail_service, briefs: list[dict], date_str: str):
    formatted = "\n\n" + ("━" * 48) + "\n\n".join(
        format_brief_for_email(b, i + 1) for i, b in enumerate(briefs)
    )
    body = f"""Good morning, {OWNER_NAME}.

Here are today's 2 creative briefs from Sam — {date_str}.
Review, pick your favorite, and hand it off to the design pipeline.

{formatted}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
— Sam, Creative Director
{BUSINESS_NAME}
"""
    subject = f"Sam's Creative Briefs — {datetime.now().strftime('%A %B %-d')}"
    draft = gmail_service.users().drafts().create(
        userId="me",
        body={"message": {
            "raw": _encode_email(DELIVERY_EMAIL, subject, body)
        }}
    ).execute()
    print(f"  [Sam] Brief draft created: {draft.get('id', 'unknown')}")


def _encode_email(to: str, subject: str, body: str) -> str:
    import base64
    from email.mime.text import MIMEText
    msg = MIMEText(body, "plain")
    msg["to"] = to
    msg["from"] = BUSINESS_EMAIL
    msg["subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()
