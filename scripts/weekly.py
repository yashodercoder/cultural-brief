"""
weekly.py — Generate weekly digest of Cultural Brief ratings.
Standalone script that generates rich weekly summary.
Can be called manually OR embedded in Monday emails.

Usage:
    python3 scripts/weekly.py          # Print plain text digest
    python3 scripts/weekly.py --html   # Print HTML digest
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Import from stats module
sys.path.insert(0, str(Path(__file__).parent))
from stats import (
    get_weekly_stats,
    get_source_affinity,
    check_milestones,
    load_feedback,
    make_bar,
    get_week_start,
)
from config import MAX_MILESTONES_SHOWN, MAX_SOURCES_IN_DIGEST


def format_date_range(week_start: str) -> str:
    """Format week as 'Feb 12-18'."""
    start = datetime.fromisoformat(week_start).replace(tzinfo=timezone.utc)
    end = start + timedelta(days=6)

    # Same month
    if start.month == end.month:
        return f"{start.strftime('%b')} {start.day}-{end.day}"
    # Different months
    else:
        return f"{start.strftime('%b %d')} - {end.strftime('%b %d')}"


def format_plain_digest(week_stats: dict, sources: list[tuple[str, int]], milestones: list[str]) -> str:
    """Format digest as plain text with ASCII art bars."""
    week_start = get_week_start()
    date_range = format_date_range(week_start)

    lines = [
        "━" * 50,
        f"📈 Your Week in Culture ({date_range})",
        "━" * 50,
        "",
    ]

    # Activity section
    if week_stats["total_ratings"] > 0:
        lines.extend([
            "📚 Activity",
            f"   • {week_stats['total_ratings']} items rated ({week_stats['days_active']} days active)",
            f"   • {week_stats['ups']} up 👍  {week_stats['downs']} down 👎  {week_stats['saves']} saved 🔖",
        ])

        if week_stats['clicks'] > 0:
            click_pct = int(week_stats['click_rate'] * 100)
            lines.append(f"   • {week_stats['clicks']} clicked through ✓ ({click_pct}% click rate)")

        lines.append("")

        # Milestones
        if milestones:
            lines.append("🎯 Milestones")
            for milestone in milestones[:MAX_MILESTONES_SHOWN]:
                lines.append(f"   {milestone}")
            lines.append("")

        # Source affinity
        if sources:
            max_count = sources[0][1] if sources else 1
            lines.append("📰 What You Actually Like")
            for source, count in sources[:MAX_SOURCES_IN_DIGEST]:
                bar = make_bar(count, max_count)
                # Pad source name to 25 chars for alignment
                source_padded = source[:25].ljust(25)
                lines.append(f"   {source_padded} {bar} {count} ups")
            lines.append("")

        # Click patterns
        if week_stats['clicks'] > 0:
            click_pct = int(week_stats['click_rate'] * 100)
            lines.append("💡 Click Patterns")
            lines.append(f"   Clicked {week_stats['clicks']}/{week_stats['total_ratings']} items ({click_pct}%)")

            # Top clicked source
            if sources:
                lines.append(f"   Top clicked source: {sources[0][0]}")
            lines.append("")

    else:
        lines.extend([
            "📚 No activity this week",
            "",
        ])

    lines.append("━" * 50)

    return "\n".join(lines)


def format_html_digest(week_stats: dict, sources: list[tuple[str, int]], milestones: list[str]) -> str:
    """Format digest as HTML for email embedding."""
    week_start = get_week_start()
    date_range = format_date_range(week_start)

    if week_stats["total_ratings"] == 0:
        return """
        <div style="padding:20px;border-top:2px solid #e5e5e5;margin-top:20px;">
          <div style="font-size:16px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">
            📈 Your Week in Culture
          </div>
          <div style="font-size:14px;color:#666;">
            No activity this week
          </div>
        </div>
        """

    html_parts = [
        '<div style="padding:20px;border-top:2px solid #e5e5e5;margin-top:20px;">',
        f'<div style="font-size:16px;font-weight:600;color:#1a1a1a;margin-bottom:16px;">',
        f'📈 Your Week in Culture ({date_range})',
        '</div>',
    ]

    # Activity
    html_parts.append('<div style="margin-bottom:16px;">')
    html_parts.append('<div style="font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">📚 Activity</div>')
    html_parts.append(f'<div style="font-size:13px;color:#444;line-height:1.6;">')
    html_parts.append(f'• {week_stats["total_ratings"]} items rated ({week_stats["days_active"]} days active)<br>')
    html_parts.append(f'• {week_stats["ups"]} up 👍 &nbsp; {week_stats["downs"]} down 👎 &nbsp; {week_stats["saves"]} saved 🔖<br>')

    if week_stats['clicks'] > 0:
        click_pct = int(week_stats['click_rate'] * 100)
        html_parts.append(f'• {week_stats["clicks"]} clicked through ✓ ({click_pct}% click rate)')

    html_parts.append('</div></div>')

    # Milestones
    if milestones:
        html_parts.append('<div style="margin-bottom:16px;">')
        html_parts.append('<div style="font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">🎯 Milestones</div>')
        html_parts.append('<div style="font-size:13px;color:#444;line-height:1.6;">')
        for milestone in milestones[:MAX_MILESTONES_SHOWN]:
            html_parts.append(f'{milestone}<br>')
        html_parts.append('</div></div>')

    # Source affinity
    if sources:
        max_count = sources[0][1] if sources else 1
        html_parts.append('<div style="margin-bottom:16px;">')
        html_parts.append('<div style="font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">📰 What You Actually Like</div>')
        html_parts.append('<div style="font-size:13px;color:#444;line-height:1.6;font-family:monospace;">')

        for source, count in sources[:MAX_SOURCES_IN_DIGEST]:
            bar_width = int((count / max_count) * 100) if max_count > 0 else 0
            html_parts.append(
                f'<div style="margin-bottom:4px;">'
                f'<div style="display:inline-block;width:180px;">{source[:25]}</div>'
                f'<div style="display:inline-block;width:100px;background:#eee;height:16px;border-radius:2px;vertical-align:middle;">'
                f'<div style="width:{bar_width}%;background:#4CAF50;height:16px;border-radius:2px;"></div>'
                f'</div> {count} ups'
                f'</div>'
            )

        html_parts.append('</div></div>')

    # Click patterns
    if week_stats['clicks'] > 0:
        click_pct = int(week_stats['click_rate'] * 100)
        html_parts.append('<div style="margin-bottom:16px;">')
        html_parts.append('<div style="font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">💡 Click Patterns</div>')
        html_parts.append('<div style="font-size:13px;color:#444;line-height:1.6;">')
        html_parts.append(f'Clicked {week_stats["clicks"]}/{week_stats["total_ratings"]} items ({click_pct}%)<br>')

        if sources:
            html_parts.append(f'Top clicked source: {sources[0][0]}')

        html_parts.append('</div></div>')

    html_parts.append('</div>')

    return "\n".join(html_parts)


def generate_weekly_digest(as_html: bool = False) -> str:
    """Generate weekly summary text.

    Args:
        as_html: If True, return HTML-formatted version for email

    Returns:
        Formatted weekly digest string
    """
    feedback = load_feedback()
    week_stats = get_weekly_stats()
    sources = get_source_affinity(weeks=1)
    milestones = check_milestones(feedback)

    if as_html:
        return format_html_digest(week_stats, sources, milestones)
    else:
        return format_plain_digest(week_stats, sources, milestones)


def main():
    """CLI entry point."""
    as_html = "--html" in sys.argv

    digest = generate_weekly_digest(as_html=as_html)
    print(digest)


if __name__ == "__main__":
    main()
