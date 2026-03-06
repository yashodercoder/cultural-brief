"""
demo_rating.py — Simulate rating today's 5 items to show the celebration
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
FEEDBACK_PATH = ROOT / "data" / "feedback.json"
BRIEFS_DIR = ROOT / "data" / "briefs"

def simulate_rating():
    """Simulate rating today's 5 items."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load today's brief
    brief_path = BRIEFS_DIR / f"{today}.json"
    if not brief_path.exists():
        print(f"No brief found for {today}")
        return

    with open(brief_path) as f:
        brief = json.load(f)

    # Load existing feedback
    if FEEDBACK_PATH.exists():
        with open(FEEDBACK_PATH) as f:
            feedback = json.load(f)
    else:
        feedback = []

    # Remove any existing ratings for these items today
    feedback = [f for f in feedback if not (f["date"] == today and any(f["item_id"] == item["id"] for item in brief))]

    # Simulate ratings based on taste profile match
    ratings = [
        ("febeea1e572b", "up", True),    # Toni Morrison - cultural criticism
        ("c8c024711ad3", "save", True),  # Issey Miyake - saved to read later
        ("af22b6bf891d", "up", False),   # Virginia Woolf - loved it
        ("05d03343b6b4", "up", True),    # Russian exile - complex interiority
        ("8ea70f6e786f", "up", True),    # Syrian memoir - late-bloomer narrative
    ]

    print(f"\n🎯 Simulating rating session for {today}...\n")

    new_ratings = 0
    for item in brief:
        # Find matching rating
        rating_info = next((r for r in ratings if item["id"].startswith(r[0])), None)
        if not rating_info:
            continue

        _, rating, clicked = rating_info

        feedback.append({
            "date": today,
            "item_id": item["id"],
            "source": item["source"],
            "title": item["title"],
            "rating": rating,
            "clicked": clicked,
        })

        # Show what was rated
        emoji = {"up": "👍", "down": "👎", "save": "🔖"}[rating]
        click_label = " + clicked ✓" if clicked else ""
        print(f"[{item['source']}] {item['title'][:60]}...")
        print(f"  → {emoji} {rating}{click_label}\n")

        new_ratings += 1

    # Save feedback
    with open(FEEDBACK_PATH, "w") as f:
        json.dump(feedback, f, indent=2)

    print(f"─ {new_ratings} rating(s) saved to {FEEDBACK_PATH.relative_to(ROOT)}")

    # Show celebration
    if new_ratings > 0:
        from rate import show_session_celebration
        show_session_celebration(today, new_ratings)


if __name__ == "__main__":
    simulate_rating()
