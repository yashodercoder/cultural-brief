"""
config.py — Centralized configuration for Cultural Brief

All magic numbers and constants should be defined here with explanatory comments.
"""

from pathlib import Path

# Project paths
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
BRIEFS_DIR = DATA_DIR / "briefs"
FEEDBACK_PATH = DATA_DIR / "feedback.json"
MILESTONES_PATH = DATA_DIR / "milestones.json"

# RSS Feed Configuration
FEED_LOOKBACK_HOURS = 72  # 3 days - many quality sources publish weekly, not daily
MAX_ITEMS_TO_SEND = 40    # Cap items sent to Claude to keep costs low and focus on recent content

# Brief Generation
TARGET_BRIEF_SIZE = 5           # Default number of items in final daily brief
MIN_SOURCE_DIVERSITY = 3        # Minimum different sources required (ideally equal to brief size)

# Dynamic brief sizing by day of week (0=Monday, 6=Sunday)
BRIEF_SIZE_BY_DAY = {
    0: 3,   # Monday - Busy start to the week
    5: 7,   # Saturday - More leisure time
    6: 7,   # Sunday - Weekend reading
    # Other days use TARGET_BRIEF_SIZE
}

# API Configuration
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"  # Fast, cost-effective for filtering
ANTHROPIC_TIMEOUT = 30          # Seconds before API call times out
ANTHROPIC_MAX_TOKENS = 512      # Sufficient for JSON response with 5 items

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT = 15            # Shorter timeout - emails are quick
RESEND_MAX_RETRIES = 3         # Retry on network failures

# Email Configuration
DEFAULT_FROM_ADDRESS = "onboarding@resend.dev"  # Free tier sender (no domain needed)

# Readwise Integration
ENABLE_READWISE_SYNC = True    # Automatically sync saved items to Readwise Reader
READWISE_API_URL = "https://readwise.io/api/v3/save/"
READWISE_TIMEOUT = 10          # Readwise API is fast

# Rating Server Configuration
# Set RATING_SERVER_URL in environment for deployed server (e.g., Railway)
# Defaults to localhost for local testing
import os
RATING_SERVER_URL = os.environ.get("RATING_SERVER_URL", "http://localhost:5000")

# Rating & Analytics
RATING_OPTIONS = {"u": "up", "d": "down", "s": "save"}
RATING_LABELS = {"up": "👍", "down": "👎", "save": "🔖"}

# Milestone Thresholds
DAILY_RATING_MILESTONES = [3, 5]      # Daily rating counts to celebrate
DAILY_CLICK_MILESTONES = [3, 5]       # Daily click-through counts
WEEKLY_RATING_MILESTONES = [10, 20]   # Weekly rating counts
WEEKLY_SAVE_MILESTONES = [5]          # Weekly save counts
WEEKLY_CLICK_MILESTONES = [10]        # Weekly click counts

# Display Configuration
MAX_MILESTONES_SHOWN = 2       # Limit celebrations to avoid overwhelming user
MAX_SOURCES_IN_DIGEST = 5      # Top N sources to show in weekly digest
SOURCE_BAR_WIDTH = 8           # Width of ASCII progress bars in weekly digest
