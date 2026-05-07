"""Alex — Design Spec Agent for Rovana Studio.

Alex takes Sam's creative briefs and engineers production-ready image
generation specs: refined prompts, style variations, and technical
parameters per product type. Output goes to the workspace for Agent 4
(image generation) to consume.
"""

import json
from datetime import datetime
from pathlib import Path

import anthropic

from config import CLAUDE_MODEL, BUSINESS_NAME, BUSINESS_EMAIL, OWNER_NAME
from gmail_client import create_draft

WORKSPACE_DIR = Path(__file__).parent.parent / "workspace"

# Imagen 3 supports these aspect ratios
POD_ASPECT_RATIOS = {
    "square_print": "1:1",       # T-shirts, mugs, stickers, most POD
    "portrait_print": "3:4",     # Posters, canvas, art prints
    "phone_wallpaper": "9:16",   # Digital wallpapers
    "landscape_print": "4:3",    # Desk mats, banners
}

ALEX_SYSTEM = f"""You are Alex, Design Spec Agent for {BUSINESS_NAME}.

Your job: take a creative brief from Sam and engineer precise, production-ready
image generation specs for Imagen 3 (Google's image generation model).

You understand:
- What makes Imagen 3 prompts effective (specific, descriptive, style-first)
- Print-on-demand production requirements (clean edges, scalable, readable at distance)
- What sells on Etsy (clear concept, strong visual hierarchy, high contrast)

Your output is always valid JSON — no markdown, no explanation."""


SPEC_SCHEMA = """
For each brief, produce a spec with this structure:

{
  "concept_name": "from the brief",
  "product_focus": "primary product type to generate for",
  "variants": [
    {
      "variant_id": "v1",
      "description": "what makes this variant different",
      "aspect_ratio": "1:1",
      "prompt": "Full, detailed Imagen 3 prompt — 2-4 sentences. Lead with style/medium, then subject, then mood/lighting/details.",
      "negative_prompt": "what to avoid: blurry, low quality, text errors, watermark, distorted, cluttered"
    }
  ]
}

Rules for prompts:
- Lead with the art style/medium (e.g. 'Flat vector illustration', 'Bold typographic design', 'Vintage screenprint aesthetic')
- Be specific about colors using the brief's palette
- Include print-specific language: 'clean white background', 'high contrast', 'scalable design', 'suitable for t-shirt print'
- 3 variants per concept: one safe/clean, one bold/experimental, one minimal

Return a JSON array of spec objects — one per brief passed in. No other text."""


def load_todays_briefs() -> list[dict] | None:
    today = datetime.now().strftime("%Y%m%d")
    brief_file = WORKSPACE_DIR / f"creative_brief_{today}.json"
    if brief_file.exists():
        return json.loads(brief_file.read_text())
    # Fall back to most recent
    files = sorted(WORKSPACE_DIR.glob("creative_brief_*.json"), reverse=True)
    if files:
        print(f"  [Alex] No brief for today — using most recent: {files[0].name}")
        return json.loads(files[0].read_text())
    return None


def save_specs(specs: list[dict]) -> Path:
    WORKSPACE_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    spec_file = WORKSPACE_DIR / f"design_specs_{today}.json"
    spec_file.write_text(json.dumps(specs, indent=2))
    return spec_file


def format_spec_for_email(spec: dict, index: int) -> str:
    lines = [
        f"CONCEPT {index}: {spec['concept_name'].upper()}",
        f"Product focus: {spec['product_focus']}",
        "",
    ]
    for v in spec.get("variants", []):
        lines += [
            f"  [{v['variant_id'].upper()}] {v['description']}",
            f"  Aspect ratio: {v['aspect_ratio']}",
            f"  Prompt:",
            f"    {v['prompt']}",
            f"  Avoid: {v['negative_prompt']}",
            "",
        ]
    return "\n".join(lines)


def generate_design_specs(gmail_service=None) -> list[dict]:
    client = anthropic.Anthropic()
    today = datetime.now()
    date_str = today.strftime("%A, %B %-d, %Y")

    print("  [Alex] Loading Sam's creative briefs...")
    briefs = load_todays_briefs()
    if not briefs:
        print("  [Alex] No creative briefs found. Run `python main.py creative-brief` first.")
        return []

    briefs_text = json.dumps(briefs, indent=2)

    user_prompt = f"""Here are today's creative briefs from Sam ({date_str}):

{briefs_text}

Engineer production-ready image generation specs for each brief.
{SPEC_SCHEMA}"""

    print("  [Alex] Engineering image generation specs...")
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
        system=ALEX_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    specs = json.loads(raw)

    spec_file = save_specs(specs)
    print(f"  [Alex] Specs saved: {spec_file}")

    if gmail_service:
        _draft_spec_email(gmail_service, specs, date_str)

    return specs


def _draft_spec_email(gmail_service, specs: list[dict], date_str: str):
    formatted = ("\n" + "━" * 48 + "\n\n").join(
        format_spec_for_email(s, i + 1) for i, s in enumerate(specs)
    )
    body = f"""Hi {OWNER_NAME},

Here are today's image generation specs from Alex — {date_str}.

Each concept has 3 variants ready to generate. Review the prompts,
then run: python chief_of_staff/main.py generate-images

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{formatted}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
— Alex, Design Spec Agent
{BUSINESS_NAME}
"""
    subject = f"Alex's Design Specs — {today_label()}"
    draft = create_draft(gmail_service, to=BUSINESS_EMAIL, subject=subject, body=body)
    print(f"  [Alex] Spec draft created: {draft.get('id', 'unknown')}")


def today_label() -> str:
    return datetime.now().strftime("%A %B %-d")
