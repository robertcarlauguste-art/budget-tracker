"""Agent 4 — Image Generation via Google Imagen 3.

Reads Alex's design specs from the workspace, generates images using
Google's Imagen 3 API, and saves them locally with a summary draft in Gmail.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

from config import BUSINESS_EMAIL, DELIVERY_EMAIL, BUSINESS_NAME, OWNER_NAME
from gmail_client import create_draft

WORKSPACE_DIR = Path(__file__).parent.parent / "workspace"
IMAGEN_MODEL = "imagen-3.0-generate-001"


def get_imagen_client() -> genai.Client:
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_AI_API_KEY not set in .env")
    return genai.Client(api_key=api_key)


def load_todays_specs() -> list[dict] | None:
    today = datetime.now().strftime("%Y%m%d")
    spec_file = WORKSPACE_DIR / f"design_specs_{today}.json"
    if spec_file.exists():
        return json.loads(spec_file.read_text())
    files = sorted(WORKSPACE_DIR.glob("design_specs_*.json"), reverse=True)
    if files:
        print(f"  [Imagen] No specs for today — using most recent: {files[0].name}")
        return json.loads(files[0].read_text())
    return None


def generate_images(gmail_service=None) -> list[Path]:
    client = get_imagen_client()
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")

    print("  [Imagen] Loading Alex's design specs...")
    specs = load_todays_specs()
    if not specs:
        print("  [Imagen] No design specs found. Run `python main.py design-spec` first.")
        return []

    output_dir = WORKSPACE_DIR / "generated" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_paths = []
    summary_lines = []

    for spec in specs:
        concept = spec["concept_name"]
        print(f"  [Imagen] Generating images for: {concept}")

        for variant in spec.get("variants", []):
            vid = variant["variant_id"]
            prompt = variant["prompt"]
            aspect_ratio = variant.get("aspect_ratio", "1:1")

            try:
                response = client.models.generate_images(
                    model=IMAGEN_MODEL,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio=aspect_ratio,
                        safety_filter_level="block_only_high",
                        person_generation="dont_allow",
                    ),
                )

                if not response.generated_images:
                    print(f"    Warning: no image returned for {concept} {vid}")
                    continue

                img_bytes = response.generated_images[0].image.image_bytes
                filename = f"{concept.lower().replace(' ', '_')}_{vid}.png"
                out_path = output_dir / filename
                out_path.write_bytes(img_bytes)
                generated_paths.append(out_path)

                summary_lines.append(
                    f"  ✓ {concept} [{vid}] — {aspect_ratio}\n"
                    f"    Saved: workspace/generated/{date_str}/{filename}"
                )
                print(f"    Saved: {out_path}")

            except Exception as e:
                print(f"    Error generating {concept} {vid}: {e}")
                summary_lines.append(f"  ✗ {concept} [{vid}] — ERROR: {e}")

    if gmail_service and generated_paths:
        _draft_summary_email(gmail_service, summary_lines, today)

    print(f"  [Imagen] Done. {len(generated_paths)} image(s) saved to {output_dir}")
    return generated_paths


def _draft_summary_email(gmail_service, summary_lines: list[str], today: datetime):
    date_str = today.strftime("%A, %B %-d, %Y")
    output_dir = f"workspace/generated/{today.strftime('%Y%m%d')}/"
    body = f"""Hi {OWNER_NAME},

Image generation complete — {date_str}.

GENERATED IMAGES
{chr(10).join(summary_lines)}

FILES LOCATION
{output_dir}

Review the images in that folder. When you're ready:
  → Hand off to Production Prep (resize, export, POD specs) [coming next]
  → Or open directly in your design tool for final touches

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
— Imagen Agent
{BUSINESS_NAME}
"""
    subject = f"Images Ready — {today.strftime('%A %B %-d')}"
    draft = create_draft(gmail_service, to=DELIVERY_EMAIL, subject=subject, body=body)
    print(f"  [Imagen] Summary draft created: {draft.get('id', 'unknown')}")
