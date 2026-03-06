# One-Click Email Ratings

Rate items directly from your Cultural Brief emails with a single click! No need to open the CLI.

## Setup

### 1. Install Flask

```bash
# Using pip (with --user flag for externally-managed environments)
pip3 install --user flask

# Or using brew
brew install python-flask

# Or using pipx (recommended for macOS)
brew install pipx
pipx install flask
```

### 2. Start the Rating Server

```bash
cd cultural-brief
python3 scripts/rating_server.py
```

You'll see:
```
============================================================
📚 Cultural Brief Rating Server
============================================================

Server running on http://localhost:5000

Click rating links in your Cultural Brief emails to rate items.
Press Ctrl+C to stop the server.

============================================================
```

**Keep this terminal window open** — the server needs to run in the background for email ratings to work.

### 3. Receive Your Cultural Brief Email

Your daily Cultural Brief emails now include three rating buttons below each item:

- 👍 **Up** — You liked this article
- 👎 **Down** — Not interested in this type of content
- 🔖 **Save** — Want to read this later (added to your reading queue)

## How It Works

1. Click any rating button in your email
2. Your browser opens and shows a confirmation page
3. The rating is automatically saved to `data/feedback.json`
4. Click-through is tracked (you clicked the link to rate, so you engaged with it)

## Usage Tips

- **Leave the server running** while you read your daily brief
- Start it in the morning, rate items throughout the day, stop it at night
- Or run it only when you're actively rating items from email
- You can still use `python3 scripts/rate.py` for CLI rating (no server needed)

## Advanced: Run Server in Background

**macOS/Linux:**
```bash
# Start in background
python3 scripts/rating_server.py &

# View running processes
ps aux | grep rating_server

# Stop when done
pkill -f rating_server.py
```

**Using screen (persistent session):**
```bash
# Start new screen session
screen -S ratings

# Run server
python3 scripts/rating_server.py

# Detach with: Ctrl+A, then D
# Reattach later with: screen -r ratings
```

## Troubleshooting

**"Connection refused" when clicking rating buttons:**
- Make sure the rating server is running (`python3 scripts/rating_server.py`)
- Check that it's listening on port 5000
- Verify no other service is using port 5000: `lsof -i :5000`

**Ratings not saving:**
- Check that `data/feedback.json` exists and is writable
- Look for error messages in the server terminal
- Try rating via CLI to verify file permissions: `python3 scripts/rate.py`

**Browser opens but shows error:**
- Verify the server is running (check terminal window)
- Make sure you're clicking from the email (not a forwarded copy)
- Check server logs for error details

## Privacy & Security

- **Local only**: The rating server runs on localhost:5000 — no external traffic
- **No tracking**: Ratings are saved locally to `data/feedback.json`, nowhere else
- **Temporary**: Server only runs when you start it, stops when you quit
- **Source code**: See `scripts/rating_server.py` for full implementation

## What's Next?

Once you've rated items, explore your reading patterns:

```bash
# View your reading queue (saved items)
python3 scripts/reading_queue.py

# See taste evolution insights
python3 scripts/taste_trends.py

# Weekly digest (automatically in Monday emails)
python3 scripts/weekly.py
```

Enjoy! 📚✨
