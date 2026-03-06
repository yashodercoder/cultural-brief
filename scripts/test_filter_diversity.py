"""
test_filter_diversity.py — Simulate filter with source diversity
Shows what the improved filter would select
"""

import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

def load_raw_items(date: str) -> list[dict]:
    path = DATA_DIR / f"raw_{date}.json"
    with open(path) as f:
        return json.load(f)

def simulate_diverse_selection(items: list[dict], n: int = 5) -> list[dict]:
    """
    Simulate Claude's selection with diversity requirement.
    Strategy: Pick items round-robin from different sources.
    """
    # Group by source
    by_source = {}
    for item in items:
        source = item['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item)

    print(f"\nAvailable sources:")
    for source, source_items in by_source.items():
        print(f"  {source}: {len(source_items)} items")

    # Round-robin selection
    selected = []
    source_names = sorted(by_source.keys())
    idx = 0

    while len(selected) < n:
        for source in source_names:
            if len(selected) >= n:
                break
            source_items = by_source[source]
            if idx < len(source_items):
                selected.append(source_items[idx])
        idx += 1

    return selected[:n]

def main():
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    raw_items = load_raw_items(today)
    print(f"📥 Loaded {len(raw_items)} raw items from {today}")

    # Simulate diverse selection
    print("\n🎯 Simulating filter with DIVERSITY requirement...")
    selected = simulate_diverse_selection(raw_items, n=5)

    print(f"\n✅ Selected {len(selected)} items with source diversity:\n")

    sources = [item['source'] for item in selected]
    source_counts = Counter(sources)

    for i, item in enumerate(selected, 1):
        print(f"{i}. [{item['source']}] {item['title'][:80]}...")

    print(f"\n📊 Source breakdown:")
    for source, count in source_counts.items():
        print(f"  {source}: {count} items")

    unique_sources = len(source_counts)
    print(f"\n🎉 {unique_sources} different sources in final brief")

    if unique_sources >= 3:
        print("✅ Good diversity! (minimum 3 sources)")
    else:
        print("⚠️  Limited source diversity (only available sources were used)")

if __name__ == "__main__":
    main()
