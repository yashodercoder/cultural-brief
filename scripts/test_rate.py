"""
test_rate.py — Verify feedback load/save/dedup logic.
Run with: python3 scripts/test_rate.py
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import rate

SAMPLE_BRIEF = [
    {"id": "aaa111", "source": "LARB", "title": "On Ferrante", "link": "https://example.com/1",
     "hook": "Complex interiority done right.", "published": "2026-02-18T08:00:00+00:00"},
    {"id": "bbb222", "source": "Vulture", "title": "The Bear Essay", "link": "https://example.com/2",
     "hook": "TV as grief literature.", "published": "2026-02-18T09:00:00+00:00"},
]


def test_feedback_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        briefs_dir = tmp / "briefs"
        briefs_dir.mkdir()
        feedback_path = tmp / "feedback.json"

        # Write mock brief
        (briefs_dir / "2026-02-18.json").write_text(json.dumps(SAMPLE_BRIEF))

        with patch.object(rate, "BRIEFS_DIR", briefs_dir), \
             patch.object(rate, "FEEDBACK_PATH", feedback_path):

            # Load brief
            brief = rate.load_brief("2026-02-18")
            assert len(brief) == 2

            # No prior feedback
            feedback = rate.load_feedback()
            assert feedback == []
            assert rate.already_rated(feedback, "aaa111", "2026-02-18") is None

            # Save a rating
            feedback.append({
                "date": "2026-02-18",
                "item_id": "aaa111",
                "source": "LARB",
                "title": "On Ferrante",
                "rating": "up",
            })
            rate.save_feedback(feedback)

            # Reload and check
            feedback2 = rate.load_feedback()
            assert len(feedback2) == 1
            existing = rate.already_rated(feedback2, "aaa111", "2026-02-18")
            assert existing is not None
            assert existing["rating"] == "up"

            # Re-rate (dedup: replace existing entry, don't duplicate)
            feedback2 = [e for e in feedback2 if not (e["item_id"] == "aaa111" and e["date"] == "2026-02-18")]
            feedback2.append({
                "date": "2026-02-18", "item_id": "aaa111",
                "source": "LARB", "title": "On Ferrante", "rating": "save",
            })
            rate.save_feedback(feedback2)

            feedback3 = rate.load_feedback()
            assert len(feedback3) == 1, f"Expected 1 after re-rate, got {len(feedback3)}"
            assert feedback3[0]["rating"] == "save"

    print("PASS — brief loads, ratings save, re-rate deduplicates correctly")


if __name__ == "__main__":
    test_feedback_roundtrip()
