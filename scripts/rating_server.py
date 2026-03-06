"""
rating_server.py — Lightweight Flask server for one-click email ratings

Receives rating clicks from email links and saves them to feedback.json.
Allows users to rate items (👍/👎/🔖) directly from email without opening CLI.

Usage:
    python3 scripts/rating_server.py        # Start server on localhost:5000

Email links format:
    http://localhost:5000/rate?item_id=abc123&rating=up&date=2026-02-18&source=NYT&title=Article+Title

Ratings: up, down, save
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from flask import Flask, request, render_template_string

from data_loader import load_feedback, save_feedback
from config import FEEDBACK_PATH, RATING_LABELS

app = Flask(__name__)

# Simple HTML template for thank you page with auto-close
THANK_YOU_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Rating Saved</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f9f9f9;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 32px 24px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 400px;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .emoji {
            font-size: 56px;
            margin-bottom: 16px;
            animation: pop 0.5s ease-out;
        }
        @keyframes pop {
            0% { transform: scale(0); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        h1 {
            color: #1a1a1a;
            font-size: 24px;
            margin: 0 0 8px;
            font-weight: 600;
        }
        .message {
            color: #666;
            font-size: 15px;
            line-height: 1.5;
            margin: 0 0 20px;
        }
        .item-info {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            margin-bottom: 16px;
        }
        .source {
            color: #999;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .title {
            color: #333;
            font-weight: 500;
        }
        .close-hint {
            color: #999;
            font-size: 13px;
            margin-top: 16px;
        }
        .close-btn {
            display: inline-block;
            padding: 10px 24px;
            background: #1a1a1a;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            margin-top: 16px;
            cursor: pointer;
            border: none;
            font-family: inherit;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">{{ emoji }}</div>
        <h1>✓ Saved!</h1>
        <div class="message">{{ success_message | safe }}</div>
        <div class="item-info">
            <div class="source">{{ item_source }}</div>
            <div class="title">{{ item_title }}</div>
        </div>
        <div class="close-hint" id="closeHint">Closing automatically...</div>
        <button class="close-btn" id="closeBtn" style="display:none;" onclick="window.close()">
            Tap to Close
        </button>
    </div>

    <script>
        // Attempt to auto-close after 1.5 seconds
        setTimeout(function() {
            // Try to close the window
            window.close();

            // If we're still here after 500ms, window.close() didn't work
            setTimeout(function() {
                // Show manual close button
                document.getElementById('closeHint').style.display = 'none';
                document.getElementById('closeBtn').style.display = 'inline-block';
            }, 500);
        }, 1500);
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Simple landing page."""
    return """
    <html>
    <head><title>Cultural Brief Rating Server</title></head>
    <body style="font-family: Georgia, serif; max-width: 600px; margin: 100px auto; text-align: center;">
        <h1>📚 Cultural Brief Rating Server</h1>
        <p>Server is running! One-click email ratings are enabled.</p>
        <p><small>Use rating links from your Cultural Brief emails to rate items.</small></p>
    </body>
    </html>
    """


@app.route("/rate")
def rate():
    """
    Handle rating clicks from email links.

    Query params:
        item_id: Unique item identifier
        rating: up, down, or save
        date: ISO date (YYYY-MM-DD)
        source: Source name (e.g., "Arts & Letters Daily")
        title: Article title
        url: Article URL (for Readwise sync)
        clicked: true (always true for email click-through)
    """
    # Extract parameters
    item_id = request.args.get("item_id")
    rating = request.args.get("rating")
    date = request.args.get("date")
    source = unquote(request.args.get("source", ""))
    title = unquote(request.args.get("title", ""))
    url = unquote(request.args.get("url", ""))

    # Validate required params
    if not item_id or not rating or not date:
        return "Error: Missing required parameters (item_id, rating, date)", 400

    if rating not in ["up", "down", "save"]:
        return f"Error: Invalid rating '{rating}'. Must be up, down, or save.", 400

    # Load existing feedback
    feedback = load_feedback()

    # Check if this item was already rated (replace old rating)
    existing = [f for f in feedback if f["item_id"] == item_id and f["date"] == date]

    if existing:
        # Update existing rating
        for f in feedback:
            if f["item_id"] == item_id and f["date"] == date:
                f["rating"] = rating
                f["clicked"] = True  # Email click-through counts as clicked
    else:
        # Add new rating
        feedback.append({
            "date": date,
            "item_id": item_id,
            "source": source,
            "title": title,
            "rating": rating,
            "clicked": True  # Email click-through counts as clicked
        })

    # Save updated feedback
    save_feedback(feedback)

    # Sync to Readwise if saved
    readwise_success = False
    if rating == "save" and url:
        try:
            from readwise_sync import save_to_readwise

            readwise_success = save_to_readwise(
                url=url,
                title=title,
                source=source,
                summary=None,  # Don't have hook in rating endpoint
                item_id=item_id
            )
        except Exception as e:
            # Don't fail the rating if Readwise sync fails
            print(f"Readwise sync failed: {e}")
            pass

    # Get emoji for display
    emoji = RATING_LABELS.get(rating, "✓")
    rating_label = rating.replace("_", " ").title()

    # Build success message
    success_message = f"Your {rating_label} rating has been recorded."
    if readwise_success:
        success_message += "<br><strong>✨ Also saved to Readwise Reader!</strong>"

    # Return thank you page
    return render_template_string(
        THANK_YOU_HTML,
        emoji=emoji,
        rating=rating_label,
        item_source=source,
        item_title=title,
        success_message=success_message
    )


if __name__ == "__main__":
    # Get port from environment (Railway sets PORT automatically)
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")  # 0.0.0.0 allows external connections

    print("=" * 60)
    print("📚 Cultural Brief Rating Server")
    print("=" * 60)
    print()
    print(f"Server running on {host}:{port}")
    print()
    print("Click rating links in your Cultural Brief emails to rate items.")
    print("Press Ctrl+C to stop the server.")
    print()
    print("=" * 60)

    # Run Flask server
    app.run(host=host, port=port, debug=False)
