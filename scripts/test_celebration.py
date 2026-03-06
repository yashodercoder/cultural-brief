"""
test_celebration.py — Demo script to test the celebration feature
Simulates rating 3 items and shows the celebration output
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
FEEDBACK_PATH = ROOT / "data" / "feedback.json"

# Import the celebration function
import sys
sys.path.insert(0, str(Path(__file__).parent))
from stats import get_today_stats, check_milestones, load_feedback

def simulate_rating_session():
    """Simulate rating a few items today."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load existing feedback
    if FEEDBACK_PATH.exists():
        with open(FEEDBACK_PATH) as f:
            feedback = json.load(f)
    else:
        feedback = []

    # Add 2 new ratings for today (simulating user rating items)
    new_ratings = [
        {
            "date": today,
            "item_id": "test_abc123",
            "source": "Test Source",
            "title": "Test Article 1",
            "rating": "up",
            "clicked": True,
        },
        {
            "date": today,
            "item_id": "test_def456",
            "source": "Test Source 2",
            "title": "Test Article 2",
            "rating": "save",
            "clicked": False,
        },
    ]

    # Remove any existing test entries from today
    feedback = [f for f in feedback if not f["item_id"].startswith("test_")]

    # Add new ratings
    feedback.extend(new_ratings)

    # Save
    with open(FEEDBACK_PATH, "w") as f:
        json.dump(feedback, f, indent=2)

    print(f"\n─ {len(new_ratings)} rating(s) saved to {FEEDBACK_PATH.relative_to(ROOT)}")

    # Show celebration
    show_session_celebration(today, len(new_ratings))


def show_session_celebration(today: str, new_ratings: int):
    """Display quick stats after rating session completes."""
    stats = get_today_stats(today)
    milestones = check_milestones(load_feedback())

    print("\n" + "━" * 50)

    # Today's stats
    rating_parts = []
    if stats['ups'] > 0:
        rating_parts.append(f"{stats['ups']}👍")
    if stats['downs'] > 0:
        rating_parts.append(f"{stats['downs']}👎")
    if stats['saves'] > 0:
        rating_parts.append(f"{stats['saves']}🔖")

    rating_str = " ".join(rating_parts) if rating_parts else "no ratings"
    click_str = f" + {stats['clicks']} clicked ✓" if stats['clicks'] > 0 else ""

    print(f"📊 Today: {stats['total']} rated ({rating_str}){click_str}")

    # Milestones (if any achieved today)
    for milestone in milestones[:2]:  # Max 2 to keep brief
        print(f"{milestone}")

    print("━" * 50)


if __name__ == "__main__":
    print("Simulating rating session...\n")
    simulate_rating_session()
