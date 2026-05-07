import anthropic

from config import (
    CLAUDE_MODEL,
    URGENT_KEYWORDS,
    VOICE_PROFILE,
    BUSINESS_NAME,
    BUSINESS_EMAIL,
    OWNER_NAME,
)
from gmail_client import (
    get_thread_messages,
    get_message_headers,
    extract_message_body,
    create_reply_draft,
    get_unanswered_threads,
    get_unread_threads_since,
)


def is_urgent(subject: str, body: str) -> bool:
    text = (subject + " " + body).lower()
    return any(kw in text for kw in URGENT_KEYWORDS)


def classify_and_draft(
    client: anthropic.Anthropic,
    service,
    thread: dict,
) -> dict | None:
    """Returns a result dict if the thread needs action, else None."""
    messages = get_thread_messages(service, thread["id"])
    if not messages:
        return None

    last_msg = messages[-1]
    headers = get_message_headers(last_msg)
    sender = headers.get("from", "Unknown Sender")
    subject = headers.get("subject", "(No Subject)")
    body = extract_message_body(last_msg)[:3000]

    # Skip threads where Robert already sent the last message
    if BUSINESS_EMAIL in sender or OWNER_NAME.lower() in sender.lower():
        return None

    urgent = is_urgent(subject, body)

    classification_prompt = f"""Classify this email for {BUSINESS_NAME} ({BUSINESS_EMAIL}).

From: {sender}
Subject: {subject}
Body (truncated):
{body}

Classify as exactly one of:
- URGENT (needs immediate attention — refund, complaint, legal, account issue)
- REPLY_NEEDED (customer question, order inquiry, collaboration, general request)
- INFORMATIONAL (newsletters, receipts, notifications — no reply needed)

Reply with only the classification word."""

    classification = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=20,
        messages=[{"role": "user", "content": classification_prompt}],
    ).content[0].text.strip().upper()

    if "URGENT" in classification:
        label = "URGENT"
    elif "REPLY" in classification:
        label = "REPLY_NEEDED"
    else:
        return None  # Informational — skip

    # Draft a reply
    draft_prompt = f"""{VOICE_PROFILE}

Draft a reply to this email for {OWNER_NAME} to review.
The reply should be concise, helpful, and written in Robert's voice.
Do NOT add subject lines, headers, or sign-off — just the body text starting with a greeting.

From: {sender}
Subject: {subject}
Their message:
{body}

Write the reply now:"""

    draft_body = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": draft_prompt}],
    ).content[0].text.strip()

    # Add sign-off
    draft_body += f"\n\nBest,\n{OWNER_NAME}\n{BUSINESS_NAME}"

    return {
        "label": label,
        "sender": sender,
        "subject": subject,
        "thread_id": thread["id"],
        "draft_body": draft_body,
    }


def process_email_check(client: anthropic.Anthropic, service, hours_ago: int = 12) -> list[dict]:
    """Check emails from the last N hours, draft replies, return results."""
    threads = get_unanswered_threads(service, hours_ago=hours_ago)
    results = []
    for thread in threads[:10]:  # Cap at 10 to avoid runaway API calls
        result = classify_and_draft(client, service, thread)
        if result:
            results.append(result)
    return results


def process_urgent_check(client: anthropic.Anthropic, service) -> list[dict]:
    """Check emails from the last 30 minutes for anything urgent."""
    threads = get_unread_threads_since(service, hours_ago=1)
    results = []
    for thread in threads[:20]:
        messages = get_thread_messages(service, thread["id"])
        if not messages:
            continue
        last_msg = messages[-1]
        headers = get_message_headers(last_msg)
        sender = headers.get("from", "")
        subject = headers.get("subject", "")
        body = extract_message_body(last_msg)[:1000]

        if BUSINESS_EMAIL in sender:
            continue

        if is_urgent(subject, body):
            result = classify_and_draft(client, service, thread)
            if result:
                result["label"] = "URGENT"
                results.append(result)
    return results


def save_reply_drafts(service, results: list[dict], urgent_prefix: bool = False) -> int:
    """Save reply drafts to Gmail. Returns count of drafts saved."""
    count = 0
    for r in results:
        subject = r["subject"]
        if urgent_prefix and r["label"] == "URGENT":
            subject = f"[URGENT — Kevin] Re: {subject}"
        try:
            create_reply_draft(
                service,
                thread_id=r["thread_id"],
                to=r["sender"],
                subject=subject,
                body=r["draft_body"],
            )
            count += 1
        except Exception as e:
            print(f"  Warning: could not save draft for '{r['subject']}': {e}")
    return count


def format_email_section(results: list[dict]) -> str:
    if not results:
        return "  • Inbox clear — no replies needed."
    lines = []
    for i, r in enumerate(results, 1):
        tag = "[URGENT] " if r["label"] == "URGENT" else ""
        lines.append(f"  {i}. {tag}From: {r['sender']}")
        lines.append(f"     Subject: {r['subject']}")
        lines.append(f"     Draft reply saved to your Drafts folder.\n")
    return "\n".join(lines)
