"""
filter.py — Single Claude Haiku call to select 5 items from today's raw fetch
and write a one-line hook for each. Output → data/briefs/YYYY-MM-DD.json.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

# Load .env for local runs; silently skipped in CI where secrets come from env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Import centralized configuration
from config import (
    ROOT, DATA_DIR, BRIEFS_DIR,
    ANTHROPIC_MODEL, ANTHROPIC_MAX_TOKENS, ANTHROPIC_TIMEOUT,
    MAX_ITEMS_TO_SEND, TARGET_BRIEF_SIZE, MIN_SOURCE_DIVERSITY,
    BRIEF_SIZE_BY_DAY
)

BRIEFS_DIR.mkdir(exist_ok=True)


def load_taste_profile() -> str:
    return (ROOT / "taste_profile.md").read_text()


def load_raw_items(date: str) -> list[dict]:
    path = DATA_DIR / f"raw_{date}.json"
    if not path.exists():
        sys.exit(f"No raw file for {date}. Run fetch.py first.")
    with open(path) as f:
        return json.load(f)


def get_previously_briefed_ids(days_back: int = 7) -> set[str]:
    """Get item IDs from recent briefs to avoid repeats."""
    from datetime import datetime, timedelta

    briefed_ids = set()
    today = datetime.now(timezone.utc)

    for i in range(1, days_back + 1):
        past_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        brief_path = BRIEFS_DIR / f"{past_date}.json"

        if brief_path.exists():
            with open(brief_path) as f:
                brief = json.load(f)
                for item in brief:
                    briefed_ids.add(item["id"])

    return briefed_ids


def get_brief_size_for_today() -> int:
    """Get the appropriate brief size based on day of week."""
    day_of_week = datetime.now(timezone.utc).weekday()
    return BRIEF_SIZE_BY_DAY.get(day_of_week, TARGET_BRIEF_SIZE)


def build_prompt(taste_profile: str, items: list[dict], brief_size: int = None) -> str:
    """Build the prompt for Claude with dynamic brief size."""
    if brief_size is None:
        brief_size = get_brief_size_for_today()
    item_lines = []
    for item in items:
        desc = item["description"].strip().replace("\n", " ")
        item_lines.append(
            f"ID: {item['id']}\n"
            f"Source: {item['source']}\n"
            f"Title: {item['title']}\n"
            f"Description: {desc[:300]}"
        )

    items_block = "\n\n---\n\n".join(item_lines)

    min_diversity = min(brief_size, MIN_SOURCE_DIVERSITY)

    return f"""{taste_profile}

---

Below are {len(items)} items fetched today. Select exactly {brief_size} DIFFERENT items that best match the taste profile above.

IMPORTANT:
- Select {brief_size} unique items (do not select the same item twice)
- MAXIMIZE SOURCE DIVERSITY: Select items from as many different sources as possible (ideally {brief_size} different sources, minimum {min_diversity})
- Avoid selecting multiple items from the same source unless absolutely necessary
- Use the EXACT item id shown (e.g., "9f75a8fe94a9", not an index number)
- Write a one-line hook (15–25 words) for each. The hook is a sharp, specific reason to read it — written like a recommendation from a smart friend, not a summary or abstract. It should make the reader feel something or want to click immediately. Be concrete and direct. Do not describe what the piece is about in general terms. Do not use words like: pivotal, underscore, foster, highlight, explore, delve, crucial, vibrant, tapestry, testament, landscape, intricate, showcase, or resonate.

BAD hook: "A deeply personal essay on masking autism and its physical toll—complex interiority meets embodied experience."
GOOD hook: "She spent years performing normalcy so convincingly her body finally gave out. This is what that costs."

BAD hook: "Paris Review explores how style becomes tyranny in writing—literary criticism that reveals craft obsession."
GOOD hook: "On the writers whose sentences are so controlled they've stopped meaning anything. A trap disguised as ambition."

- Assign a "type" to each item. Pick exactly one from this list: books, film, music, tv, art, interview, poetry, ideas, games, food, theatre

Return ONLY a JSON array with exactly {brief_size} items, no other text:
[
  {{"id": "<exact item id from list>", "hook": "<one-line hook>", "type": "<type>"}},
  {{"id": "<exact item id from list>", "hook": "<one-line hook>", "type": "<type>"}},
  {{"id": "<exact item id from list>", "hook": "<one-line hook>", "type": "<type>"}},
  {{"id": "<exact item id from list>", "hook": "<one-line hook>", "type": "<type>"}},
  {{"id": "<exact item id from list>", "hook": "<one-line hook>", "type": "<type>"}}
]

Items:

{items_block}"""


def extract_json_from_response(text: str) -> str:
    """Extract JSON array from Claude's response, handling markdown code fences robustly."""
    text = text.strip()

    # Try to find JSON within markdown code fences using regex
    json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    # If no code fence, check if the text itself is valid JSON
    if text.startswith('[') and text.endswith(']'):
        return text

    # Last resort: look for array anywhere in text
    array_match = re.search(r'(\[.*\])', text, re.DOTALL)
    if array_match:
        return array_match.group(1)

    return text  # Return as-is and let JSON parser fail with clear error


def call_haiku(prompt: str) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("❌ Error: ANTHROPIC_API_KEY environment variable not set")

    # Validate API key format
    if not api_key.startswith("sk-ant-") or len(api_key) < 20:
        sys.exit("❌ Error: ANTHROPIC_API_KEY appears malformed (should start with 'sk-ant-')")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=ANTHROPIC_MAX_TOKENS,
            timeout=ANTHROPIC_TIMEOUT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Extract JSON robustly
        json_text = extract_json_from_response(text)
        return json.loads(json_text)

    except anthropic.APIError as e:
        sys.exit(f"❌ Anthropic API error: {e}")
    except json.JSONDecodeError as e:
        sys.exit(f"❌ Failed to parse Claude's response as JSON.\n"
                f"Error: {e}\n"
                f"Response preview: {text[:300]}...")
    except Exception as e:
        sys.exit(f"❌ Unexpected error calling Claude: {e}")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = BRIEFS_DIR / f"{today}.json"

    if out_path.exists():
        print(f"Brief already exists for {today}: {out_path}")
        return

    taste_profile = load_taste_profile()
    raw_items = load_raw_items(today)

    if not raw_items:
        sys.exit("No items to filter. Check that fetch.py produced results.")

    # Get appropriate brief size for today
    brief_size = get_brief_size_for_today()
    day_name = datetime.now(timezone.utc).strftime("%A")

    # Exclude items from recent briefs (avoid repeats)
    previously_briefed = get_previously_briefed_ids(days_back=7)
    fresh_items = [item for item in raw_items if item["id"] not in previously_briefed]

    print(f"Total items: {len(raw_items)}, Fresh items: {len(fresh_items)} (filtered {len(previously_briefed)} already briefed)")

    if len(fresh_items) < brief_size:
        print(f"⚠️  Warning: Only {len(fresh_items)} fresh items available (need {brief_size}). Including some repeats.")
        fresh_items = raw_items  # Fall back to all items if not enough fresh ones

    # Trim to cap — prioritise variety by keeping first N (already deduped by source in fetch)
    items_to_send = fresh_items[:MAX_ITEMS_TO_SEND]
    print(f"Sending {len(items_to_send)} items to Haiku ({day_name}: {brief_size} item brief)...")

    prompt = build_prompt(taste_profile, items_to_send, brief_size)
    selections = call_haiku(prompt)

    # Map selections back to full item data
    id_to_item = {item["id"]: item for item in items_to_send}
    brief = []
    seen_ids = set()  # Track IDs to prevent duplicates

    for sel in selections:
        item_id = sel["id"]

        # Skip if we've already added this item
        if item_id in seen_ids:
            print(f"  Warning: duplicate id {item_id!r} — skipping")
            continue

        item = id_to_item.get(item_id)
        if not item:
            print(f"  Warning: unknown id {item_id!r} — skipping")
            continue

        brief.append({**item, "hook": sel["hook"], "type": sel.get("type", "")})
        seen_ids.add(item_id)

    # Validate we have the expected number of items
    if len(brief) < brief_size:
        sys.exit(f"Error: Only got {len(brief)} valid items (need {brief_size}). Claude may have returned invalid IDs or duplicates. Check the logs above.")

    with open(out_path, "w") as f:
        json.dump(brief, f, indent=2)

    print(f"Brief: {len(brief)} items → {out_path}")
    for item in brief:
        print(f"\n  [{item['source']}] {item['title']}")
        print(f"  {item['hook']}")


if __name__ == "__main__":
    main()
