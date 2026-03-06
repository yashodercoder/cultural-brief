"""
reading_queue.py — Generate a monthly digest of saved items

Creates a beautiful reading list from all 🔖 saved items, organized by theme,
with estimated reading times and smart recommendations.

Usage:
    python3 scripts/reading_queue.py           # Current month
    python3 scripts/reading_queue.py --month 2 # Specific month (1-12)
    python3 scripts/reading_queue.py --all     # All saved items ever
"""

import argparse
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

from config import FEEDBACK_PATH
from stats import load_feedback


def get_saved_items(month: int = None, year: int = None) -> list[dict]:
    """Get all saved items, optionally filtered by month/year."""
    feedback = load_feedback()

    saved = [f for f in feedback if f["rating"] == "save"]

    if month and year:
        saved = [
            f for f in saved
            if datetime.fromisoformat(f["date"]).month == month
            and datetime.fromisoformat(f["date"]).year == year
        ]

    return saved


def categorize_by_source(items: list[dict]) -> dict[str, list[dict]]:
    """Group saved items by source."""
    by_source = defaultdict(list)
    for item in items:
        by_source[item["source"]].append(item)
    return dict(sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True))


def estimate_reading_time(items: list[dict]) -> int:
    """Rough estimate: average article is 10 minutes."""
    return len(items) * 10


def generate_reading_queue_text(month: int = None, all_time: bool = False) -> str:
    """Generate plain text reading queue."""
    today = datetime.now(timezone.utc)

    if all_time:
        saved_items = get_saved_items()
        title = "Your Complete Reading Queue"
    elif month:
        saved_items = get_saved_items(month=month, year=today.year)
        month_name = datetime(today.year, month, 1).strftime("%B")
        title = f"Your {month_name} Reading Queue"
    else:
        # Current month
        saved_items = get_saved_items(month=today.month, year=today.year)
        title = f"Your {today.strftime('%B')} Reading Queue"

    if not saved_items:
        return f"\n📚 {title}\n\n   No saved items yet!\n"

    lines = [
        "=" * 60,
        f"📚 {title}",
        "=" * 60,
        "",
        f"📊 {len(saved_items)} saved items",
        f"⏱️  Estimated reading time: ~{estimate_reading_time(saved_items)} minutes",
        "",
    ]

    # Group by source
    by_source = categorize_by_source(saved_items)

    lines.append("📖 BY SOURCE:")
    lines.append("")

    for source, items in by_source.items():
        lines.append(f"  {source} ({len(items)} items)")
        for item in items:
            date = datetime.fromisoformat(item["date"]).strftime("%b %d")
            # Truncate long titles
            title_truncated = item["title"][:70] + "..." if len(item["title"]) > 70 else item["title"]
            lines.append(f"    • [{date}] {title_truncated}")
        lines.append("")

    # Recommendation based on pattern
    lines.append("💡 START HERE:")
    lines.append("")

    # Recommend the most-saved source
    top_source = list(by_source.keys())[0]
    top_items = by_source[top_source]

    lines.append(f"  You saved {len(top_items)} items from {top_source}.")
    lines.append(f"  Start with: {top_items[0]['title'][:60]}...")
    lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def generate_reading_queue_html(month: int = None, all_time: bool = False) -> str:
    """Generate HTML reading queue for email."""
    today = datetime.now(timezone.utc)

    if all_time:
        saved_items = get_saved_items()
        title = "Your Complete Reading Queue"
    elif month:
        saved_items = get_saved_items(month=month, year=today.year)
        month_name = datetime(today.year, month, 1).strftime("%B")
        title = f"Your {month_name} Reading Queue"
    else:
        saved_items = get_saved_items(month=today.month, year=today.year)
        title = f"Your {today.strftime('%B')} Reading Queue"

    if not saved_items:
        return f"<div><strong>📚 {title}</strong><br>No saved items yet!</div>"

    by_source = categorize_by_source(saved_items)

    html_parts = [
        '<div style="padding:20px;font-family:Georgia,serif;">',
        f'<h2 style="color:#1a1a1a;">📚 {title}</h2>',
        f'<p style="color:#666;">',
        f'  {len(saved_items)} saved items • ~{estimate_reading_time(saved_items)} min reading time',
        f'</p>',
    ]

    for source, items in by_source.items():
        html_parts.append(f'<h3 style="color:#1a1a1a;margin-top:24px;">{source} ({len(items)} items)</h3>')
        html_parts.append('<ul style="line-height:1.8;">')

        for item in items:
            date = datetime.fromisoformat(item["date"]).strftime("%b %d")
            html_parts.append(
                f'<li><strong>[{date}]</strong> {item["title"]}</li>'
            )

        html_parts.append('</ul>')

    # Recommendation
    top_source = list(by_source.keys())[0]
    top_items = by_source[top_source]

    html_parts.append('<div style="background:#f5f5f5;padding:16px;margin-top:24px;border-radius:4px;">')
    html_parts.append('<strong>💡 Start Here:</strong><br>')
    html_parts.append(f'You saved {len(top_items)} items from {top_source}. ')
    html_parts.append(f'Start with: <em>{top_items[0]["title"]}</em>')
    html_parts.append('</div>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate reading queue from saved items")
    parser.add_argument("--month", type=int, help="Month number (1-12)")
    parser.add_argument("--all", action="store_true", help="Show all saved items")
    parser.add_argument("--html", action="store_true", help="Output HTML format")
    args = parser.parse_args()

    if args.html:
        print(generate_reading_queue_html(month=args.month, all_time=args.all))
    else:
        print(generate_reading_queue_text(month=args.month, all_time=args.all))


if __name__ == "__main__":
    main()
