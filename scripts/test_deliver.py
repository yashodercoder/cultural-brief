"""
test_deliver.py — Verify email formatting (no network call).
Run with: python3 scripts/test_deliver.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import deliver

SAMPLE_BRIEF = [
    {
        "id": "aaa111",
        "source": "LARB",
        "title": "On Ferrante and the Problem of Likability",
        "link": "https://example.com/ferrante",
        "hook": "Ferrante's heroines resist being understood — this essay asks why that unsettles us.",
        "description": "...",
        "published": "2026-02-18T08:00:00+00:00",
    },
    {
        "id": "ccc333",
        "source": "Vulture",
        "title": "How The Bear Became Television's Most Anxious Text",
        "link": "https://example.com/bear",
        "hook": "The Bear as grief literature: kitchen as the place where men perform emotion sideways.",
        "description": "...",
        "published": "2026-02-18T09:00:00+00:00",
    },
]


def test_plain_format():
    out = deliver.format_plain(SAMPLE_BRIEF, "February 18, 2026")
    assert "Cultural Brief — February 18, 2026" in out
    assert "LARB" in out
    assert "Ferrante" in out
    assert "https://example.com/ferrante" in out
    assert "rate.py" in out
    print("PASS — plain text format")


def test_html_format():
    out = deliver.format_html(SAMPLE_BRIEF, "February 18, 2026")
    assert "<html>" in out
    assert "Vulture" in out
    assert "The Bear" in out
    assert "https://example.com/bear" in out
    print("PASS — HTML format")


if __name__ == "__main__":
    test_plain_format()
    test_html_format()
    print()
    # Print preview
    print(deliver.format_plain(SAMPLE_BRIEF, "February 18, 2026"))
