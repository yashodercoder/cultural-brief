"""
discover_sources.py — Automated source discovery using Claude

Finds new RSS sources similar to your taste profile and top-rated sources.
Runs monthly to keep your Cultural Brief fresh with new voices.

Usage:
    python3 scripts/discover_sources.py              # Discover 10 new sources
    python3 scripts/discover_sources.py --count 20   # Discover 20 new sources
    python3 scripts/discover_sources.py --auto-add   # Automatically add to sources.yaml
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import feedparser
import yaml

# Load .env for local runs
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from config import ROOT, ANTHROPIC_MODEL, ANTHROPIC_TIMEOUT
from stats import load_feedback, get_source_affinity


def load_taste_profile() -> str:
    """Load the user's taste profile."""
    return (ROOT / "taste_profile.md").read_text()


def load_current_sources() -> list[str]:
    """Load list of current source names from sources.yaml."""
    with open(ROOT / "sources.yaml") as f:
        data = yaml.safe_load(f)
    return [source["name"] for source in data["rss"]]


def get_top_rated_sources(weeks: int = 4) -> list[str]:
    """Get sources that user has rated highly recently."""
    try:
        affinity = get_source_affinity(weeks=weeks)
        return [source for source, count in affinity[:10]]  # Top 10 sources
    except:
        return []


def build_discovery_prompt(
    taste_profile: str,
    current_sources: list[str],
    top_rated: list[str],
    count: int = 10
) -> str:
    """Build prompt for Claude to discover new sources."""

    current_list = "\n".join(f"  - {s}" for s in current_sources[:30])  # Sample
    top_rated_list = "\n".join(f"  - {s}" for s in top_rated) if top_rated else "  (No rating data yet)"

    return f"""You are helping discover new RSS sources for a curated reading newsletter.

USER'S TASTE PROFILE:
{taste_profile}

CURRENT SOURCES ({len(current_sources)} total):
{current_list}
...and {len(current_sources) - 30} more

TOP-RATED SOURCES (user loves these):
{top_rated_list}

TASK:
Find {count} NEW sources that match the taste profile above. Focus on:
1. Publications similar to top-rated sources
2. High-quality literary, cultural, film/TV criticism
3. Sources user doesn't already have
4. Active publications with working RSS feeds
5. Mix of prestige, academic, international, and emerging voices

For each source, provide:
- Name (exact publication name)
- RSS Feed URL (must be valid RSS/Atom feed)
- Category (literary, film, academic, etc.)
- Why it fits (1 sentence explaining match to taste profile)

Return ONLY a JSON array with exactly {count} sources:
[
  {{
    "name": "Publication Name",
    "url": "https://example.com/feed/",
    "category": "literary",
    "reason": "Matches taste for atmospheric criticism and high/low intersections"
  }},
  ...
]

IMPORTANT:
- Do NOT suggest sources already in the current sources list
- Only suggest sources with RSS feeds (not just websites)
- Prioritize active publications (not defunct magazines)
- Match the sophisticated, essayistic tone of the taste profile
"""


def discover_sources_with_claude(
    taste_profile: str,
    current_sources: list[str],
    top_rated: list[str],
    count: int = 10
) -> list[dict]:
    """Use Claude to discover new sources."""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("❌ Error: ANTHROPIC_API_KEY environment variable not set")

    prompt = build_discovery_prompt(taste_profile, current_sources, top_rated, count)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            timeout=ANTHROPIC_TIMEOUT * 2,  # Discovery takes longer
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Extract JSON (handle markdown fences)
        import re
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        sources = json.loads(text)
        return sources

    except anthropic.APIError as e:
        sys.exit(f"❌ Anthropic API error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Claude's response as JSON.")
        print(f"Response preview: {text[:500]}...")
        sys.exit(1)
    except Exception as e:
        sys.exit(f"❌ Unexpected error: {e}")


def test_rss_feed(url: str) -> tuple[bool, str]:
    """Test if RSS feed is valid and accessible.

    Returns:
        (is_valid, error_message)
    """
    try:
        feed = feedparser.parse(url)

        # Check for errors
        if hasattr(feed, 'bozo') and feed.bozo:
            return (False, f"Feed parse error: {feed.bozo_exception}")

        # Check if feed has entries
        if not feed.entries:
            return (False, "Feed has no entries")

        # Success!
        return (True, f"✓ {len(feed.entries)} entries")

    except Exception as e:
        return (False, f"Error: {e}")


def validate_discovered_sources(sources: list[dict]) -> list[dict]:
    """Test RSS feeds and filter out broken ones."""

    print(f"\nValidating {len(sources)} discovered sources...")
    print()

    valid_sources = []

    for source in sources:
        name = source["name"]
        url = source["url"]

        print(f"Testing: {name}")
        print(f"  URL: {url}")

        is_valid, message = test_rss_feed(url)

        if is_valid:
            print(f"  {message}")
            valid_sources.append(source)
        else:
            print(f"  ✗ {message}")

        print()

    return valid_sources


def add_sources_to_yaml(sources: list[dict], category: str = None):
    """Add new sources to sources.yaml file."""

    yaml_path = ROOT / "sources.yaml"

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    # Add discovery timestamp comment
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Add sources
    for source in sources:
        data["rss"].append({
            "name": source["name"],
            "url": source["url"],
        })

    # Write back
    with open(yaml_path, "w") as f:
        f.write(f"# Last auto-discovery: {timestamp} ({len(sources)} sources added)\n")
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Added {len(sources)} sources to sources.yaml")


def main():
    parser = argparse.ArgumentParser(description="Discover new RSS sources")
    parser.add_argument("--count", type=int, default=10, help="Number of sources to discover")
    parser.add_argument("--auto-add", action="store_true", help="Automatically add validated sources to sources.yaml")
    parser.add_argument("--skip-validation", action="store_true", help="Skip RSS feed validation (faster)")
    args = parser.parse_args()

    print("=" * 60)
    print("🔍 Cultural Brief Source Discovery")
    print("=" * 60)
    print()

    # Load data
    print("Loading taste profile and current sources...")
    taste_profile = load_taste_profile()
    current_sources = load_current_sources()
    top_rated = get_top_rated_sources(weeks=4)

    print(f"  Current sources: {len(current_sources)}")
    print(f"  Top-rated sources: {len(top_rated)}")
    print()

    # Discover sources
    print(f"Discovering {args.count} new sources with Claude...")
    print()

    discovered = discover_sources_with_claude(
        taste_profile=taste_profile,
        current_sources=current_sources,
        top_rated=top_rated,
        count=args.count
    )

    print(f"✅ Claude suggested {len(discovered)} sources")
    print()

    # Validate feeds
    if not args.skip_validation:
        valid_sources = validate_discovered_sources(discovered)
        print(f"✅ {len(valid_sources)}/{len(discovered)} sources have working RSS feeds")
    else:
        valid_sources = discovered
        print("⚠️  Skipping validation (--skip-validation)")

    print()
    print("=" * 60)
    print("DISCOVERED SOURCES:")
    print("=" * 60)
    print()

    for i, source in enumerate(valid_sources, 1):
        print(f"{i}. {source['name']}")
        print(f"   Category: {source['category']}")
        print(f"   URL: {source['url']}")
        print(f"   Why: {source['reason']}")
        print()

    # Auto-add if requested
    if args.auto_add:
        if valid_sources:
            add_sources_to_yaml(valid_sources)
            print()
            print("✅ Run fetch.py to test the new sources!")
        else:
            print("⚠️  No valid sources to add")
    else:
        print("💡 To add these sources, run with --auto-add")
        print("   Or manually add them to sources.yaml")


if __name__ == "__main__":
    main()
