from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.readonly",
]

# Business identity
OWNER_NAME = "Robert"
BUSINESS_NAME = "Rovana Studio"
BUSINESS_EMAIL = "rovanastudio@gmail.com"
PERSONAL_EMAIL = "Robert.carl.auguste@gmail.com"

# Where Kevin/Sam/Alex deliver drafts — set to whichever Gmail was authorized via OAuth
DELIVERY_EMAIL = PERSONAL_EMAIL

# Email urgency keywords (case-insensitive)
URGENT_KEYWORDS = [
    "refund", "urgent", "problem", "issue", "complaint", "dmca",
    "not received", "wrong item", "damaged", "dispute", "chargeback",
    "cancel", "broken", "error", "help",
]

# Robert's voice profile — injected into every Claude prompt that drafts emails
VOICE_PROFILE = """
You are drafting emails on behalf of Robert Auguste, CEO of Rovana Studio,
an Etsy shop specializing in digital and print-on-demand products.

Robert's writing style:
- Direct, confident, and entrepreneurial
- Short paragraphs — no fluff, no filler
- Professional but warm and personable
- Always signs off as "Robert"
- Never uses corporate jargon or hollow phrases like "I hope this email finds you well"
- Gets to the point in the first sentence
- If there's a problem, he owns it immediately and offers a clear solution
"""

# Daily briefing priorities (fixed)
TOP_3_PRIORITIES = [
    "Create or refine designs based on today's 5 ideas below",
    "Review trending memes and slogans — pick 1-2 to repurpose for the shop this week",
    "Handle all emails in your Drafts folder",
]

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"
