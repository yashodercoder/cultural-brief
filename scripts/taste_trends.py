"""
taste_trends.py — Monthly taste evolution insights

Analyzes how your reading tastes and patterns are changing over time.
Shows trends, discoveries, and evolving preferences.

Usage:
    python3 scripts/taste_trends.py              # Current month vs last month
    python3 scripts/taste_trends.py --months 3   # Last 3 months trend
    python3 scripts/taste_trends.py --html       # HTML format for email
"""

import argparse
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from pathlib import Path

from config import FEEDBACK_PATH
from stats import load_feedback, get_source_affinity


def get_items_in_month(feedback: list[dict], year: int, month: int) -> list[dict]:
    """Get all rated items from a specific month."""
    return [
        f for f in feedback
        if datetime.fromisoformat(f["date"]).year == year
        and datetime.fromisoformat(f["date"]).month == month
    ]


def calculate_engagement_score(items: list[dict]) -> float:
    """Calculate engagement score (0-100) based on clicks and saves."""
    if not items:
        return 0.0

    clicks = sum(1 for f in items if f.get("clicked", False))
    saves = sum(1 for f in items if f["rating"] == "save")

    click_rate = (clicks / len(items)) * 100
    save_rate = (saves / len(items)) * 100

    # Weighted: clicks are 70%, saves are 30%
    return (click_rate * 0.7) + (save_rate * 0.3)


def get_top_sources(items: list[dict], top_n: int = 5) -> list[tuple[str, int]]:
    """Get top N sources by 'up' ratings."""
    ups = [f for f in items if f["rating"] == "up"]
    source_counts = Counter(f["source"] for f in ups)
    return source_counts.most_common(top_n)


def find_new_sources(current_items: list[dict], prev_items: list[dict]) -> list[str]:
    """Find sources that appeared this month but not last month."""
    current_sources = set(f["source"] for f in current_items if f["rating"] == "up")
    prev_sources = set(f["source"] for f in prev_items if f["rating"] == "up")
    return sorted(current_sources - prev_sources)


def generate_trends_text(months: int = 2) -> str:
    """Generate plain text taste trends report."""
    feedback = load_feedback()

    if not feedback:
        return "\n📊 Taste Trends\n\n   Not enough data yet. Rate more items!\n"

    today = datetime.now(timezone.utc)

    # Get current and previous month
    current_month = get_items_in_month(feedback, today.year, today.month)
    prev_month_date = today.replace(day=1) - timedelta(days=1)
    prev_month = get_items_in_month(feedback, prev_month_date.year, prev_month_date.month)

    if not current_month and not prev_month:
        return "\n📊 Taste Trends\n\n   Not enough data yet. Rate more items!\n"

    lines = [
        "=" * 60,
        f"📊 Your Taste Evolution - {today.strftime('%B %Y')}",
        "=" * 60,
        "",
    ]

    # Activity comparison
    if prev_month:
        change = len(current_month) - len(prev_month)
        change_pct = (change / len(prev_month) * 100) if prev_month else 0
        direction = "📈" if change > 0 else "📉" if change < 0 else "→"

        lines.append("📚 READING ACTIVITY:")
        lines.append(f"   This month: {len(current_month)} items rated")
        lines.append(f"   Last month: {len(prev_month)} items rated")
        lines.append(f"   {direction} {abs(change_pct):.0f}% {'more' if change > 0 else 'less' if change < 0 else 'same'}")
        lines.append("")

    # Engagement trends
    if current_month and prev_month:
        current_engagement = calculate_engagement_score(current_month)
        prev_engagement = calculate_engagement_score(prev_month)
        engagement_change = current_engagement - prev_engagement

        lines.append("💡 ENGAGEMENT:")
        lines.append(f"   Current: {current_engagement:.0f}/100")
        lines.append(f"   Last month: {prev_engagement:.0f}/100")

        if abs(engagement_change) > 5:
            direction = "🔥" if engagement_change > 0 else "📉"
            lines.append(f"   {direction} {abs(engagement_change):.0f} point {'increase' if engagement_change > 0 else 'decrease'}")
        else:
            lines.append("   → Steady engagement")
        lines.append("")

    # Source evolution
    if current_month:
        top_sources = get_top_sources(current_month, top_n=3)

        lines.append("⭐ WHAT YOU'RE LOVING:")
        for source, count in top_sources:
            lines.append(f"   • {source} ({count} ups)")
        lines.append("")

    # New discoveries
    if current_month and prev_month:
        new_sources = find_new_sources(current_month, prev_month)

        if new_sources:
            lines.append("🆕 NEW SOURCES YOU DISCOVERED:")
            for source in new_sources[:3]:
                lines.append(f"   • {source}")
            lines.append("")

    # Pattern insights
    if current_month:
        # Days of week analysis
        day_counts = Counter(
            datetime.fromisoformat(f["date"]).strftime("%A")
            for f in current_month
        )
        top_day = day_counts.most_common(1)[0]

        lines.append("📅 READING PATTERNS:")
        lines.append(f"   You rated most on {top_day[0]}s ({top_day[1]} items)")

        # Click-through by source
        clicked = [f for f in current_month if f.get("clicked", False)]
        if clicked:
            click_rate = len(clicked) / len(current_month) * 100
            lines.append(f"   You clicked through {click_rate:.0f}% of items")

        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def generate_trends_html(months: int = 2) -> str:
    """Generate HTML taste trends for email."""
    feedback = load_feedback()

    if not feedback:
        return "<div><strong>📊 Taste Trends</strong><br>Not enough data yet.</div>"

    today = datetime.now(timezone.utc)
    current_month = get_items_in_month(feedback, today.year, today.month)
    prev_month_date = today.replace(day=1) - timedelta(days=1)
    prev_month = get_items_in_month(feedback, prev_month_date.year, prev_month_date.month)

    html_parts = [
        '<div style="padding:20px;font-family:Georgia,serif;">',
        f'<h2 style="color:#1a1a1a;">📊 Your Taste Evolution - {today.strftime("%B %Y")}</h2>',
    ]

    # Activity
    if prev_month and current_month:
        change = len(current_month) - len(prev_month)
        change_pct = (change / len(prev_month) * 100) if prev_month else 0
        direction = "📈" if change > 0 else "📉" if change < 0 else "→"

        html_parts.append('<div style="margin-bottom:20px;">')
        html_parts.append('<strong>📚 Reading Activity</strong><br>')
        html_parts.append(f'This month: {len(current_month)} items<br>')
        html_parts.append(f'Last month: {len(prev_month)} items<br>')
        html_parts.append(f'{direction} <strong>{abs(change_pct):.0f}%</strong> {"more" if change > 0 else "less" if change < 0 else "same"}')
        html_parts.append('</div>')

    # Engagement
    if current_month and prev_month:
        current_engagement = calculate_engagement_score(current_month)
        prev_engagement = calculate_engagement_score(prev_month)

        html_parts.append('<div style="margin-bottom:20px;">')
        html_parts.append('<strong>💡 Engagement Score</strong><br>')
        html_parts.append(f'<span style="font-size:32px;font-weight:bold;color:#4CAF50;">{current_engagement:.0f}</span>/100')
        html_parts.append(f'<br><small>(Last month: {prev_engagement:.0f})</small>')
        html_parts.append('</div>')

    # Top sources
    if current_month:
        top_sources = get_top_sources(current_month, top_n=3)

        html_parts.append('<div style="margin-bottom:20px;">')
        html_parts.append('<strong>⭐ What You\'re Loving</strong><br>')
        html_parts.append('<ul style="margin:8px 0;">')
        for source, count in top_sources:
            html_parts.append(f'<li>{source} ({count} ups)</li>')
        html_parts.append('</ul>')
        html_parts.append('</div>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate taste evolution insights")
    parser.add_argument("--months", type=int, default=2, help="Number of months to analyze")
    parser.add_argument("--html", action="store_true", help="Output HTML format")
    args = parser.parse_args()

    if args.html:
        print(generate_trends_html(months=args.months))
    else:
        print(generate_trends_text(months=args.months))


if __name__ == "__main__":
    main()
