"""
readwise_sync.py — Sync saved items to Readwise Reader

Automatically sends saved (🔖) items to your Readwise Reader inbox.
Works with both CLI ratings and one-click email ratings.

Setup:
    1. Get your Readwise access token: https://readwise.io/access_token
    2. Add to .env: READWISE_API_TOKEN=your_token_here
    3. Enable in config.py: ENABLE_READWISE_SYNC = True

Usage:
    # Automatically called when you save an item
    # Or manually sync all saved items:
    python3 scripts/readwise_sync.py --sync-all
"""

import os
import sys
from pathlib import Path
from typing import Optional

import httpx

# Load .env for local runs
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from config import ENABLE_READWISE_SYNC, READWISE_API_URL, READWISE_TIMEOUT

# Shared HTTPX client for connection pooling (reuses TCP connections)
_http_client = None

def get_http_client() -> httpx.Client:
    """Get or create shared HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=READWISE_TIMEOUT)
    return _http_client


def get_readwise_token() -> Optional[str]:
    """Get Readwise API token from environment."""
    token = os.environ.get("READWISE_API_TOKEN")
    # Strip whitespace/newlines (common when copy-pasting tokens)
    return token.strip() if token else None


def save_to_readwise(
    url: str,
    title: str,
    source: str = None,
    summary: str = None,
    item_id: str = None
) -> bool:
    """
    Save an article to Readwise Reader.

    Args:
        url: Article URL
        title: Article title
        source: Source name (e.g., "Arts & Letters Daily")
        summary: Optional description/hook
        item_id: Optional internal item ID for tracking

    Returns:
        True if saved successfully, False otherwise
    """
    if not ENABLE_READWISE_SYNC:
        return False

    token = get_readwise_token()
    if not token:
        print("⚠️  Readwise API token not found. Set READWISE_API_TOKEN in .env")
        return False

    try:
        # Build request payload
        payload = {
            "url": url,
            "title": title,
            "saved_using": "Cultural Brief",
        }

        # Add optional fields
        if source:
            payload["author"] = source

        if summary:
            payload["summary"] = summary

        # Note: Removed 'location' field - Readwise API doesn't accept custom values

        # Send to Readwise Reader API (using shared client for connection pooling)
        client = get_http_client()
        response = client.post(
            READWISE_API_URL,
            headers={
                "Authorization": f"Token {token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        response.raise_for_status()

        # Success!
        print(f"✅ Saved to Readwise: {title[:60]}...")
        return True

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print(f"❌ Readwise authentication failed. Check your API token.")
        elif e.response.status_code == 400:
            print(f"❌ Invalid request to Readwise: {e.response.text}")
        else:
            print(f"❌ Readwise API error ({e.response.status_code}): {e.response.text}")
        return False

    except httpx.TimeoutException:
        print(f"⚠️  Readwise request timed out. Article may not be saved.")
        return False

    except Exception as e:
        print(f"❌ Error saving to Readwise: {e}")
        return False


def sync_saved_items_to_readwise():
    """
    Sync all saved items from feedback.json to Readwise Reader.
    Useful for bulk import or re-syncing after enabling Readwise.
    """
    from stats import load_feedback

    feedback = load_feedback()
    saved_items = [f for f in feedback if f["rating"] == "save"]

    if not saved_items:
        print("No saved items found in feedback.json")
        return

    print(f"Found {len(saved_items)} saved items. Syncing to Readwise...")
    print()

    success_count = 0
    fail_count = 0

    # Load raw items to get URLs (feedback.json doesn't store URLs)
    # We'll need to match by item_id
    from datetime import datetime
    import json

    for item in saved_items:
        date = item["date"]
        item_id = item["item_id"]

        # Try to find the full item data from the brief
        brief_path = Path(__file__).parent.parent / "data" / "briefs" / f"{date}.json"

        if not brief_path.exists():
            print(f"⚠️  Brief not found for {date}, skipping {item['title'][:40]}...")
            fail_count += 1
            continue

        with open(brief_path) as f:
            brief_items = json.load(f)

        # Find matching item
        full_item = next((i for i in brief_items if i["id"] == item_id), None)

        if not full_item:
            print(f"⚠️  Item {item_id} not found in brief, skipping...")
            fail_count += 1
            continue

        # Sync to Readwise
        if save_to_readwise(
            url=full_item["link"],
            title=full_item["title"],
            source=full_item["source"],
            summary=full_item.get("hook"),
            item_id=item_id
        ):
            success_count += 1
        else:
            fail_count += 1

    print()
    print("=" * 60)
    print(f"Sync complete: {success_count} saved, {fail_count} failed")
    print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sync saved items to Readwise Reader")
    parser.add_argument("--sync-all", action="store_true", help="Sync all saved items from feedback.json")
    args = parser.parse_args()

    if args.sync_all:
        sync_saved_items_to_readwise()
    else:
        print("Usage: python3 scripts/readwise_sync.py --sync-all")
        print()
        print("Or enable ENABLE_READWISE_SYNC in config.py for automatic syncing.")


if __name__ == "__main__":
    main()
