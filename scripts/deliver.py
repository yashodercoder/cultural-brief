"""
deliver.py — Format today's brief and send via Resend.
Reads data/briefs/YYYY-MM-DD.json, sends a plain + HTML email.

Required env vars:
  RESEND_API_KEY  — from resend.com
  BRIEF_FROM      — verified sender address, e.g. brief@yourdomain.com (optional, defaults to onboarding@resend.dev)
  BRIEF_TO        — recipient address
"""

import html
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Load .env for local runs; silently skipped in CI where secrets come from env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Import centralized configuration
from config import (
    ROOT, BRIEFS_DIR,
    RESEND_API_URL, RESEND_TIMEOUT, RESEND_MAX_RETRIES,
    DEFAULT_FROM_ADDRESS,
    RATING_SERVER_URL
)

# Shared HTTPX client for connection pooling (reuses TCP connections)
_http_client = None

def get_http_client() -> httpx.Client:
    """Get or create shared HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=RESEND_TIMEOUT)
    return _http_client


def load_brief(date: str) -> list[dict]:
    path = BRIEFS_DIR / f"{date}.json"
    if not path.exists():
        sys.exit(f"No brief for {date}. Run filter.py first.")
    with open(path) as f:
        return json.load(f)


def format_title(title: str) -> str:
    """Clean up RSS feed titles for proper punctuation"""
    title = title.strip()

    # If title doesn't end with punctuation, add a period
    if title and title[-1] not in '.!?"\'"':
        title += "."

    return title


def add_tracking(url: str, item_id: str) -> str:
    """Add tracking parameters to URLs for click-through analytics"""
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}utm_source=cultural-brief&utm_item={item_id}"


def format_plain(brief: list[dict], date_label: str, weekly_footer: str = "") -> str:
    """Generate plain text email.

    Args:
        brief: List of 5 items
        date_label: "February 18, 2026"
        weekly_footer: Optional plain text weekly digest to append
    """
    lines = [f"Cultural Brief — {date_label}", "=" * 40, ""]
    for i, item in enumerate(brief, 1):
        tracked_url = add_tracking(item['link'], item['id'])
        lines += [
            f"{i}. [{item['source']}] {format_title(item['title'])}",
            f"   {item['hook']}",
            f"   {tracked_url}",
            "",
        ]
    lines += ["—", "One-click ratings: Start rating server with `python3 scripts/rating_server.py`"]
    lines += ["Or rate via CLI: python3 scripts/rate.py"]

    # Append weekly digest if provided
    if weekly_footer:
        lines.append("")
        lines.append(weekly_footer)

    return "\n".join(lines)


def format_html(brief: list[dict], date_label: str, weekly_footer: str = "", today: str = None) -> str:
    """Generate HTML email.

    Args:
        brief: List of 5 items
        date_label: "February 18, 2026"
        weekly_footer: Optional HTML weekly digest to append
        today: Today's date in YYYY-MM-DD format (for rating links)
    """
    from urllib.parse import quote

    # Color Palette - Soft pastels rotating per item
    PASTEL_COLORS = ['#fff5f5', '#f0f9ff', '#fffbeb', '#f0fdf4', '#faf5ff', '#fef3f2', '#ecfeff']
    SECONDARY_TEXT = "#64748b"
    TITLE_TEXT = "#1e293b"
    BODY_TEXT = "#475569"
    PAGE_BG = "#fafafa"
    DIVIDER = "#e5e5e5"

    items_html = ""
    for i, item in enumerate(brief):
        bg_color = PASTEL_COLORS[i % len(PASTEL_COLORS)]
        tracked_url = add_tracking(item['link'], item['id'])
        formatted_title = format_title(item['title'])

        # Escape HTML entities to prevent injection and formatting issues
        safe_source = html.escape(item['source'])
        safe_title = html.escape(formatted_title)
        safe_hook = html.escape(item['hook'])

        # Build one-click rating links
        rating_links = ""
        if today:
            base_url = f"{RATING_SERVER_URL}/rate"
            url_encoded_source = quote(item['source'])
            url_encoded_title = quote(item['title'])
            url_encoded_link = quote(item['link'])

            up_url = f"{base_url}?item_id={item['id']}&rating=up&date={today}&source={url_encoded_source}&title={url_encoded_title}&url={url_encoded_link}"
            down_url = f"{base_url}?item_id={item['id']}&rating=down&date={today}&source={url_encoded_source}&title={url_encoded_title}&url={url_encoded_link}"
            save_url = f"{base_url}?item_id={item['id']}&rating=save&date={today}&source={url_encoded_source}&title={url_encoded_title}&url={url_encoded_link}"

            rating_links = f"""
            <div style="display:flex;gap:20px;font-size:20px;margin-top:16px;">
              <a href="{up_url}" style="text-decoration:none;">👍</a>
              <a href="{down_url}" style="text-decoration:none;">👎</a>
              <a href="{save_url}" style="text-decoration:none;">🔖</a>
            </div>"""

        items_html += f"""
        <tr>
          <td style="padding:0 0 8px 0;">
            <div style="background:{bg_color};padding:24px;">
              <div style="font-size:11px;color:{SECONDARY_TEXT};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">
                {safe_source}
              </div>
              <div style="margin-bottom:12px;">
                <a href="{tracked_url}" style="font-size:19px;font-weight:600;color:{TITLE_TEXT};text-decoration:none;line-height:1.4;display:block;">
                  {safe_title}
                </a>
              </div>
              <div style="font-size:16px;color:{BODY_TEXT};line-height:1.7;">
                {safe_hook}
              </div>
              {rating_links}
            </div>
          </td>
        </tr>"""

    # Add weekly footer if provided
    if weekly_footer:
        items_html += f"""
        <tr>
          <td style="padding-top:32px;border-top:1px solid {DIVIDER};margin-top:32px;">
            {weekly_footer}
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:{PAGE_BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE_BG};">
    <tr><td align="center" style="padding:20px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;background:#fff;padding:40px;">
        <tr>
          <td style="padding-bottom:24px;border-bottom:1px solid {DIVIDER};margin-bottom:32px;">
            <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:8px;">
              Cultural Brief
            </div>
            <div style="font-size:28px;font-weight:700;color:#0f172a;">
              {date_label}
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding-top:32px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              {items_html}
            </table>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send(subject: str, plain: str, html: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        sys.exit("❌ Error: RESEND_API_KEY environment variable not set")

    to_addr = os.environ.get("BRIEF_TO")
    if not to_addr:
        sys.exit("❌ Error: BRIEF_TO environment variable not set")

    # Handle empty string from GitHub secrets (GitHub sets empty secrets as empty string, not None)
    from_addr = os.environ.get("BRIEF_FROM") or DEFAULT_FROM_ADDRESS

    # Retry logic with exponential backoff
    client = get_http_client()
    for attempt in range(RESEND_MAX_RETRIES):
        try:
            resp = client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "from": from_addr,
                    "to": [to_addr],
                    "subject": subject,
                    "text": plain,
                    "html": html,
                    "tags": [{"name": "type", "value": "cultural-brief"}],
                },
            )
            resp.raise_for_status()
            email_id = resp.json().get('id')
            print(f"✅ Sent → {to_addr} (id: {email_id})")
            print(f"📊 Track clicks at: https://resend.com/emails/{email_id}")
            return  # Success!

        except httpx.HTTPStatusError as e:
            # Parse error message for actionable advice
            try:
                error_data = e.response.json()
                error_msg = error_data.get('message', e.response.text)
            except:
                error_msg = e.response.text

            # Provide specific guidance based on error type
            if 'domain' in error_msg.lower() or 'verify' in error_msg.lower():
                sys.exit(f"❌ Email domain not verified.\n"
                        f"   Fix: Visit https://resend.com/domains to verify your domain.\n"
                        f"   Or use the free sender: onboarding@resend.dev\n"
                        f"   Details: {error_msg}")
            elif 'rate limit' in error_msg.lower():
                if attempt < RESEND_MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️  Rate limited. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                sys.exit(f"❌ Rate limited after {RESEND_MAX_RETRIES} attempts. Try again later.")
            elif e.response.status_code == 403:
                sys.exit(f"❌ Authentication failed or permission denied.\n"
                        f"   Check: RESEND_API_KEY is correct and not expired.\n"
                        f"   Details: {error_msg}")
            else:
                sys.exit(f"❌ Resend API error ({e.response.status_code}): {error_msg}")

        except httpx.TimeoutException:
            if attempt < RESEND_MAX_RETRIES - 1:
                wait_time = 2 ** attempt
                print(f"⚠️  Request timed out. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            sys.exit(f"❌ Request timed out after {RESEND_MAX_RETRIES} attempts.")

        except Exception as e:
            sys.exit(f"❌ Unexpected error sending email: {e}")


def is_monday() -> bool:
    """Check if today is Monday."""
    return datetime.now(timezone.utc).weekday() == 0


def format_date_label(date_obj: datetime) -> str:
    """Format date as 'February 18, 2026' (cross-platform compatible)."""
    # Avoid %-d which is Unix-only
    formatted = date_obj.strftime("%B %d, %Y")
    # Remove leading zero from day (e.g., "February 08" -> "February 8")
    return formatted.replace(" 0", " ")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_label = format_date_label(datetime.now(timezone.utc))

    brief = load_brief(today)

    # Check if Monday and append weekly digest
    weekly_digest_plain = ""
    weekly_digest_html = ""

    if is_monday():
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from weekly import generate_weekly_digest
            weekly_digest_plain = "\n\n" + generate_weekly_digest(as_html=False)
            weekly_digest_html = generate_weekly_digest(as_html=True)
        except ImportError:
            # Gracefully skip if weekly module not available
            pass

    plain = format_plain(brief, date_label, weekly_digest_plain)
    html = format_html(brief, date_label, weekly_digest_html, today)

    print(plain)  # preview in CI logs
    send(subject=f"Cultural Brief — {date_label}", plain=plain, html=html)


if __name__ == "__main__":
    main()
