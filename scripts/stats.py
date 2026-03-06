"""
stats.py — Analytics engine for Cultural Brief ratings.
Pure computation module that processes feedback.json and returns structured data.
No API calls, no side effects (except milestone tracking).
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

from data_loader import load_feedback
from config import (
    ROOT, FEEDBACK_PATH, MILESTONES_PATH,
    DAILY_RATING_MILESTONES, DAILY_CLICK_MILESTONES,
    WEEKLY_RATING_MILESTONES, WEEKLY_SAVE_MILESTONES, WEEKLY_CLICK_MILESTONES,
    MAX_MILESTONES_SHOWN, MAX_SOURCES_IN_DIGEST, SOURCE_BAR_WIDTH
)



def load_milestones() -> dict:
    """Load achieved milestones."""
    if not MILESTONES_PATH.exists():
        return {"last_updated": "", "achieved": []}
    with open(MILESTONES_PATH) as f:
        return json.load(f)


def save_milestones(data: dict) -> None:
    """Save milestones to disk."""
    MILESTONES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MILESTONES_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_today_stats(date: str) -> dict:
    """Return stats for items rated today.

    Returns: {
        'total': 5,
        'ups': 3,
        'downs': 1,
        'saves': 1,
        'clicks': 2
    }
    """
    feedback = load_feedback()
    today_items = [f for f in feedback if f["date"] == date]

    stats = {
        "total": len(today_items),
        "ups": sum(1 for f in today_items if f["rating"] == "up"),
        "downs": sum(1 for f in today_items if f["rating"] == "down"),
        "saves": sum(1 for f in today_items if f["rating"] == "save"),
        "clicks": sum(1 for f in today_items if f.get("clicked", False)),
    }
    return stats


def get_week_start(date_str: str = None) -> str:
    """Get Monday of the week containing date_str (or today).

    Args:
        date_str: ISO date string "YYYY-MM-DD" or None for today

    Returns:
        ISO date string of the Monday
    """
    if date_str:
        date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    else:
        date = datetime.now(timezone.utc)

    # Get Monday (0 = Monday, 6 = Sunday)
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    return monday.strftime("%Y-%m-%d")


def get_weekly_stats(start_date: str = None) -> dict:
    """Return stats for current or specified week.

    Args:
        start_date: Monday of the week to analyze, or None for current week

    Returns: {
        'total_ratings': 18,
        'ups': 12,
        'downs': 4,
        'saves': 2,
        'clicks': 8,
        'days_active': 5,
        'top_sources': [('Arts & Letters Daily', 8), ('LARB', 5)],
        'click_rate': 0.44  # 8/18
    }
    """
    feedback = load_feedback()

    # Get week boundaries
    if start_date is None:
        start_date = get_week_start()

    start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end = start + timedelta(days=7)

    # Filter to this week
    week_items = [
        f for f in feedback
        if start <= datetime.fromisoformat(f["date"]).replace(tzinfo=timezone.utc) < end
    ]

    if not week_items:
        return {
            "total_ratings": 0,
            "ups": 0,
            "downs": 0,
            "saves": 0,
            "clicks": 0,
            "days_active": 0,
            "top_sources": [],
            "click_rate": 0.0,
        }

    # Count stats
    ups = sum(1 for f in week_items if f["rating"] == "up")
    downs = sum(1 for f in week_items if f["rating"] == "down")
    saves = sum(1 for f in week_items if f["rating"] == "save")
    clicks = sum(1 for f in week_items if f.get("clicked", False))

    # Days active
    unique_dates = set(f["date"] for f in week_items)
    days_active = len(unique_dates)

    # Top sources (by ups only)
    source_ups = defaultdict(int)
    for f in week_items:
        if f["rating"] == "up":
            source_ups[f["source"]] += 1

    top_sources = sorted(source_ups.items(), key=lambda x: x[1], reverse=True)

    # Click rate
    click_rate = clicks / len(week_items) if week_items else 0.0

    return {
        "total_ratings": len(week_items),
        "ups": ups,
        "downs": downs,
        "saves": saves,
        "clicks": clicks,
        "days_active": days_active,
        "top_sources": top_sources,
        "click_rate": click_rate,
    }


def get_source_affinity(weeks: int = 1) -> list[tuple[str, int]]:
    """Return sources ranked by 'up' count in recent N weeks.

    Args:
        weeks: Number of recent weeks to analyze

    Returns:
        [('Arts & Letters Daily', 8), ('LARB', 5), ...]
    """
    feedback = load_feedback()

    # Calculate cutoff date
    cutoff = datetime.now(timezone.utc) - timedelta(days=weeks * 7)

    # Filter to recent weeks
    recent = [
        f for f in feedback
        if datetime.fromisoformat(f["date"]).replace(tzinfo=timezone.utc) >= cutoff
        and f["rating"] == "up"
    ]

    # Count by source
    source_counts = defaultdict(int)
    for f in recent:
        source_counts[f["source"]] += 1

    return sorted(source_counts.items(), key=lambda x: x[1], reverse=True)


def is_milestone_achieved(key: str, week_start: str, milestones: dict) -> bool:
    """Check if milestone was already achieved this week."""
    for entry in milestones.get("achieved", []):
        # Weekly milestones: check if achieved in same week
        if key.startswith("weekly_"):
            entry_week = get_week_start(entry["date"])
            if entry["key"] == key and entry_week == week_start:
                return True
        # Daily milestones: check if achieved on same day
        elif key.startswith("daily_"):
            if entry["key"] == key and entry["date"] == week_start:
                return True
        # Other milestones: once ever
        elif entry["key"] == key:
            return True
    return False


def check_milestones(feedback: list[dict] = None) -> list[str]:
    """Detect newly achieved milestones.

    Returns:
        ['🎯 10 ratings this week', '⭐ 5 clicks today']

    Milestone thresholds defined in config.py
    """
    if feedback is None:
        feedback = load_feedback()

    if not feedback:
        return []

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_start = get_week_start(today)

    milestones = load_milestones()
    new_milestones = []

    # Get current stats
    today_stats = get_today_stats(today)
    week_stats = get_weekly_stats(week_start)

    # Build milestone definitions from config
    milestone_defs = []

    # Daily rating milestones
    for threshold in sorted(DAILY_RATING_MILESTONES, reverse=True):
        milestone_defs.append((
            f"daily_{threshold}",
            threshold,
            today_stats["total"],
            today,
            f"🎯 {threshold} ratings today"
        ))

    # Daily click milestones
    for threshold in sorted(DAILY_CLICK_MILESTONES, reverse=True):
        milestone_defs.append((
            f"daily_clicks_{threshold}",
            threshold,
            today_stats["clicks"],
            today,
            f"⭐ {threshold} clicks today"
        ))

    # Weekly rating milestones
    for threshold in sorted(WEEKLY_RATING_MILESTONES, reverse=True):
        milestone_defs.append((
            f"weekly_{threshold}",
            threshold,
            week_stats["total_ratings"],
            week_start,
            f"⭐ {threshold} ratings this week"
        ))

    # Weekly save milestones
    for threshold in WEEKLY_SAVE_MILESTONES:
        milestone_defs.append((
            f"saves_{threshold}",
            threshold,
            week_stats["saves"],
            week_start,
            f"🔖 {threshold} saves this week"
        ))

    # Weekly click milestones
    for threshold in WEEKLY_CLICK_MILESTONES:
        milestone_defs.append((
            f"clicks_{threshold}",
            threshold,
            week_stats["clicks"],
            week_start,
            f"✓ {threshold} clicks this week"
        ))

    for key, threshold, actual, ref_date, label in milestone_defs:
        if actual >= threshold and not is_milestone_achieved(key, ref_date, milestones):
            new_milestones.append((key, label, ref_date))

    # Save newly achieved milestones
    if new_milestones:
        for key, label, ref_date in new_milestones:
            milestones.setdefault("achieved", []).append({
                "date": ref_date,
                "key": key,
                "label": label,
            })
        milestones["last_updated"] = today
        save_milestones(milestones)

    # Return labels only
    return [label for _, label, _ in new_milestones]


def make_bar(count: int, max_count: int, width: int = None) -> str:
    """Create ASCII progress bar: ████████ for source affinity."""
    if width is None:
        width = SOURCE_BAR_WIDTH
    if max_count == 0:
        return ""
    filled = int((count / max_count) * width)
    return "█" * filled


if __name__ == "__main__":
    # Quick test when run directly
    print("Today's stats:", get_today_stats(datetime.now(timezone.utc).strftime("%Y-%m-%d")))
    print("Weekly stats:", get_weekly_stats())
    print("Milestones:", check_milestones())
