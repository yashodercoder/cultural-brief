"""
data_loader.py — Centralized data loading functions

Single source of truth for loading feedback, briefs, and sources.
Eliminates 6+ duplicate load_feedback() functions across codebase.
"""

import json
from pathlib import Path
from typing import Optional

import yaml

from config import ROOT, BRIEFS_DIR, FEEDBACK_PATH


def load_feedback() -> list[dict]:
    """
    Load all feedback ratings from feedback.json.

    Returns:
        List of rating dictionaries with keys: date, item_id, source, title, rating, clicked
    """
    # Ensure parent directory exists (important for Railway/fresh deployments)
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not FEEDBACK_PATH.exists():
        return []

    with open(FEEDBACK_PATH) as f:
        return json.load(f)


def save_feedback(feedback: list[dict]) -> None:
    """
    Save feedback ratings to feedback.json.

    Args:
        feedback: List of rating dictionaries
    """
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(FEEDBACK_PATH, "w") as f:
        json.dump(feedback, f, indent=2)


def load_brief(date: str) -> list[dict]:
    """
    Load a specific day's brief.

    Args:
        date: ISO date string (YYYY-MM-DD)

    Returns:
        List of brief items with keys: id, source, title, link, description, published, hook
    """
    path = BRIEFS_DIR / f"{date}.json"

    if not path.exists():
        raise FileNotFoundError(f"No brief found for {date}")

    with open(path) as f:
        return json.load(f)


def load_sources() -> list[dict]:
    """
    Load RSS sources from sources.yaml.

    Returns:
        List of source dictionaries with keys: name, url
    """
    with open(ROOT / "sources.yaml") as f:
        return yaml.safe_load(f)["rss"]


def load_taste_profile() -> str:
    """
    Load the user's taste profile.

    Returns:
        Taste profile markdown content
    """
    return (ROOT / "taste_profile.md").read_text()
