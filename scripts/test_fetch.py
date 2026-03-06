"""
test_fetch.py — Verify fetch parsing logic against a local mock feed.
Run with: python3 scripts/test_fetch.py
"""

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import feedparser

# Add scripts dir to path so we can import fetch
sys.path.insert(0, str(Path(__file__).parent))
import fetch

def _make_mock_feed():
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    recent1 = (now - timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    recent2 = (now - timedelta(hours=4)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    old = (now - timedelta(days=8)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Mock Literary Feed</title>
            <item>
              <title>The Slow Burn of Elena Ferrante's Latest</title>
              <link>https://example.com/ferrante-review</link>
              <description>A deep look at interiority and domestic life in Ferrante's new novel.</description>
              <pubDate>{recent1}</pubDate>
            </item>
            <item>
              <title>27 Books to Read Before You Die</title>
              <link>https://example.com/listicle</link>
              <description>A listicle of must-read books.</description>
              <pubDate>{recent2}</pubDate>
            </item>
            <item>
              <title>Old Item From Last Week</title>
              <link>https://example.com/old-item</link>
              <description>This should be filtered out by the 24h cutoff.</description>
              <pubDate>{old}</pubDate>
            </item>
          </channel>
        </rss>
    """)


def test_parsing():
    from datetime import datetime, timezone, timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    source = {"name": "Mock Feed", "url": "http://mock"}

    with patch("feedparser.parse", return_value=feedparser.parse(_make_mock_feed())):
        items = fetch.fetch_source(source, cutoff)

    assert len(items) == 2, f"Expected 2 recent items, got {len(items)}"
    assert items[0]["title"] == "The Slow Burn of Elena Ferrante's Latest"
    assert items[0]["source"] == "Mock Feed"
    assert items[0]["id"]  # has an id
    assert items[1]["title"] == "27 Books to Read Before You Die"
    print("PASS — parsed 2 recent items, correctly dropped 1 old item")
    print(json.dumps(items[0], indent=2))


if __name__ == "__main__":
    test_parsing()
