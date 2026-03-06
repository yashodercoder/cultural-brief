"""
rate.py — Interactive CLI to rate today's brief items.
Run after reading the email: python3 scripts/rate.py

Keys: u = 👍 up  |  d = 👎 down  |  s = 🔖 save  |  enter = skip
Also tracks: c = clicked through to read
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import (
    ROOT, BRIEFS_DIR, FEEDBACK_PATH,
    RATING_OPTIONS as RATINGS,
    RATING_LABELS as LABELS,
    MAX_MILESTONES_SHOWN
)
from data_loader import load_brief, load_feedback, save_feedback


def already_rated(feedback: list[dict], item_id: str, date: str) -> dict | None:
    for entry in feedback:
        if entry["item_id"] == item_id and entry["date"] == date:
            return entry
    return None


def show_session_celebration(today: str, new_ratings: int):
    """Display quick stats after rating session completes."""
    try:
        from stats import get_today_stats, check_milestones, load_feedback
    except ImportError:
        return  # Gracefully skip if stats module not available

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
    for milestone in milestones[:MAX_MILESTONES_SHOWN]:
        print(f"{milestone}")

    print("━" * 50)


def prompt_rating(item: dict, index: int, total: int, existing: dict | None) -> tuple[str | None, bool]:
    """Prompt for rating and click-through. Returns (rating, clicked)."""
    label = f"[{index}/{total}]"
    source_title = f"{item['source']} — {item['title']}"
    hook = item.get("hook", "")

    print(f"\n{label} {source_title}")
    if hook:
        print(f"     {hook}")
    print(f"     {item['link']}")

    # Ask about click-through first (most objective signal)
    clicked = False
    if existing and "clicked" in existing:
        print(f"     Clicked: {'✓ yes' if existing['clicked'] else '✗ no'}")
        click_input = input("     Update click? (y/n/enter to keep) » ").strip().lower()
        if click_input == 'y':
            clicked = True
        elif click_input == 'n':
            clicked = False
        else:
            clicked = existing["clicked"]
    else:
        click_input = input("     Did you click through? (y/n) » ").strip().lower()
        clicked = click_input == 'y'

    # Then ask for rating
    if existing:
        print(f"     Already rated: {LABELS[existing['rating']]}")
        raw = input("     Re-rate? (u/d/s/enter to keep) » ").strip().lower()
        if not raw:
            return (None, clicked)
    else:
        raw = input("     Rate: (u)p / (d)own / (s)ave / enter to skip » ").strip().lower()

    return (RATINGS.get(raw), clicked)


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    brief = load_brief(today)
    feedback = load_feedback()
    new_ratings = 0

    print(f"\nCultural Brief — {today}  ({len(brief)} items)")
    print("─" * 50)

    for i, item in enumerate(brief, 1):
        existing = already_rated(feedback, item["id"], today)
        rating, clicked = prompt_rating(item, i, len(brief), existing)

        # If neither rating nor click changed, skip
        if rating is None and (existing and existing.get("clicked") == clicked):
            continue

        # Remove old entry for this item if updating
        feedback = [e for e in feedback if not (e["item_id"] == item["id"] and e["date"] == today)]

        # Use existing rating if not changing it
        final_rating = rating if rating else (existing["rating"] if existing else None)

        if final_rating:  # Only save if there's a rating
            feedback.append({
                "date": today,
                "item_id": item["id"],
                "source": item["source"],
                "title": item["title"],
                "rating": final_rating,
                "clicked": clicked,
            })
            click_label = " + clicked ✓" if clicked else ""
            print(f"     {LABELS[final_rating]} saved{click_label}")
            new_ratings += 1

            # Sync to Readwise if saved
            if final_rating == "save":
                try:
                    from readwise_sync import save_to_readwise
                    save_to_readwise(
                        url=item["link"],
                        title=item["title"],
                        source=item["source"],
                        summary=item.get("hook"),
                        item_id=item["id"]
                    )
                except ImportError:
                    pass  # Readwise module not available, skip
                except Exception as e:
                    print(f"     ⚠️  Readwise sync failed: {e}")

    save_feedback(feedback)
    print(f"\n─ {new_ratings} rating(s) saved to {FEEDBACK_PATH.relative_to(ROOT)}")

    # Show celebration if any ratings were made
    if new_ratings > 0:
        show_session_celebration(today, new_ratings)


if __name__ == "__main__":
    main()
