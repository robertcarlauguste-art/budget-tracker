import json
import time
import anthropic

from config import CLAUDE_MODEL, BUSINESS_NAME


def _run_research_prompt(client: anthropic.Anthropic, prompt: str) -> str:
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1500,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}],
            )
            text_parts = []
            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
            return "\n".join(text_parts).strip()
        except anthropic.RateLimitError:
            if attempt < 2:
                wait = 60 * (attempt + 1)
                print(f"  [Kevin] Rate limit hit — waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise


def get_design_ideas(client: anthropic.Anthropic) -> str:
    prompt = f"""You are the research assistant for {BUSINESS_NAME}, an Etsy shop selling
digital downloads and print-on-demand products.

Search the web RIGHT NOW for what's trending today in:
- Print-on-demand niches (POD)
- Digital planner / printable templates
- Wall art trends
- Motivational quote designs
- Seasonal / holiday upcoming themes

Then give me exactly 5 specific, actionable design ideas the shop can create this week.
Format each idea as:
IDEA [number]: [Catchy concept name]
Niche: [target audience]
What to make: [specific product description — be concrete]
Why now: [1 sentence on why this is timely]

Be specific. No generic advice. These should be ideas Robert can start designing today."""

    return _run_research_prompt(client, prompt)


def get_trending_memes(client: anthropic.Anthropic) -> str:
    prompt = f"""You are the content research assistant for {BUSINESS_NAME}, an Etsy shop
selling digital and print-on-demand products.

Search the web RIGHT NOW for:
- Memes trending TODAY on Reddit, Twitter/X, Instagram
- Viral slogans or phrases people are repeating this week
- Pop culture references that are at peak popularity right now

Then give me 5 memes or slogans that could be legally repurposed as original artwork
for an Etsy print-on-demand shop (no direct copying — just the concept/theme/mood).

Format each as:
TREND [number]: [Meme or slogan name/description]
Why it's hot: [1 sentence]
How to repurpose for Etsy: [specific product idea that captures the vibe legally]
Risk level: Low / Medium (flag anything that might be trademarked)

Focus on what's actually trending RIGHT NOW, not evergreen content."""

    return _run_research_prompt(client, prompt)
