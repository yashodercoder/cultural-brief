"""
notify_failure.py — Send email notification when workflow fails
"""

import os
import sys
from datetime import datetime, timezone

import httpx

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
BRIEF_TO = os.environ.get("BRIEF_TO")
# Handle empty string from GitHub secrets (GitHub sets empty secrets as empty string, not None)
BRIEF_FROM = os.environ.get("BRIEF_FROM") or "onboarding@resend.dev"


def send_failure_notification(step_name: str, error_details: str = ""):
    """Send email notification about workflow failure"""
    if not RESEND_API_KEY or not BRIEF_TO:
        print("Warning: Missing RESEND_API_KEY or BRIEF_TO - cannot send notification")
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    subject = f"⚠️ Cultural Brief Failed — {today}"

    body = f"""Your daily cultural brief workflow failed.

Failed step: {step_name}
Date: {today}
Time: {datetime.now(timezone.utc).strftime("%H:%M UTC")}

{error_details if error_details else "Check GitHub Actions logs for details."}

View workflow runs: https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'your-repo')}/actions
"""

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": BRIEF_FROM,
                "to": [BRIEF_TO],
                "subject": subject,
                "text": body,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        print(f"Failure notification sent to {BRIEF_TO}")
    except Exception as e:
        print(f"Failed to send notification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    details = sys.argv[2] if len(sys.argv) > 2 else ""
    send_failure_notification(step, details)
