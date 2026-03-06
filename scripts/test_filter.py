"""
test_filter.py — Verify filter logic with a mocked Haiku response.
Run with: python3 scripts/test_filter.py
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))
import filter as f

MOCK_ITEMS = [
    {
        "id": "aaa111",
        "source": "LARB",
        "title": "On Ferrante and the Problem of Likability",
        "link": "https://example.com/ferrante",
        "description": "A close reading of interiority in Ferrante's Neapolitan novels.",
        "published": "2026-02-18T08:00:00+00:00",
    },
    {
        "id": "bbb222",
        "source": "NYT Books",
        "title": "27 Books to Read Before You Die",
        "link": "https://example.com/listicle",
        "description": "A listicle of classics.",
        "published": "2026-02-18T07:00:00+00:00",
    },
    {
        "id": "ccc333",
        "source": "Vulture",
        "title": "How The Bear Became Television's Most Anxious Text",
        "link": "https://example.com/bear",
        "description": "Prestige TV meets culinary obsession meets grief.",
        "published": "2026-02-18T09:00:00+00:00",
    },
    {
        "id": "ddd444",
        "source": "LRB",
        "title": "Slowness as Resistance: On Mary Oliver's Late Work",
        "link": "https://example.com/oliver",
        "description": "Poetry that demands you stop and look.",
        "published": "2026-02-18T06:00:00+00:00",
    },
    {
        "id": "eee555",
        "source": "On Being",
        "title": "Krista Tippett on the Art of Listening",
        "link": "https://example.com/tippett",
        "description": "A meditation on presence and conversation.",
        "published": "2026-02-18T10:00:00+00:00",
    },
]

MOCK_HAIKU_RESPONSE = json.dumps([
    {"id": "aaa111", "hook": "Ferrante's heroines resist being understood — this essay asks why that unsettles us more than it should."},
    {"id": "ccc333", "hook": "The Bear as grief literature: how a kitchen becomes a place where men perform emotion sideways."},
    {"id": "ddd444", "hook": "Oliver's late poems are an argument that attention itself is a moral act."},
    {"id": "eee555", "hook": "Tippett on what it means to actually hear someone — rarer and harder than it sounds."},
    {"id": "bbb222", "hook": "A listicle, but the framing is oddly earnest about what reading does to a life."},
])


def make_mock_response(text):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def test_full_pipeline():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response(MOCK_HAIKU_RESPONSE)

    with patch("filter.anthropic.Anthropic", return_value=mock_client), \
         patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):

        selections = f.call_haiku("dummy prompt")
        id_to_item = {item["id"]: item for item in MOCK_ITEMS}
        brief = []
        for sel in selections:
            item = id_to_item.get(sel["id"])
            if item:
                brief.append({**item, "hook": sel["hook"]})

    assert len(brief) == 5, f"Expected 5 items, got {len(brief)}"
    assert brief[0]["id"] == "aaa111"
    assert "Ferrante" in brief[0]["hook"]
    assert all("hook" in item for item in brief)
    print("PASS — 5 items selected, hooks merged correctly")
    for item in brief:
        print(f"  [{item['source']}] {item['title']}")
        print(f"  → {item['hook']}")


if __name__ == "__main__":
    test_full_pipeline()
