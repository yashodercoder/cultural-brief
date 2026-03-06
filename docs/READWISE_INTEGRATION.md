# Readwise Integration

Automatically sync saved (🔖) items from your Cultural Brief to Readwise Reader for seamless reading and highlighting.

## Why Readwise?

[Readwise Reader](https://readwise.io/read) is a powerful read-it-later app with:
- **Clean reading experience** — Distraction-free articles
- **Highlighting & notes** — Mark important passages
- **Cross-device sync** — Read on phone, tablet, desktop
- **Email digests** — Daily review of highlights
- **Integration** — Exports to Notion, Obsidian, etc.

When you save an item in your Cultural Brief, it automatically appears in your Readwise Reader inbox!

## Setup (5 minutes)

### 1. Get Your Readwise API Token

1. Visit: https://readwise.io/access_token
2. Copy your token (starts with something like `4wZpXXXXXXXXXXXXXXXXXXXXXX`)

### 2. Add Token to Environment

**Option A: Using .env file (local)**
```bash
cd cultural-brief
echo 'READWISE_API_TOKEN=your_token_here' >> .env
```

**Option B: Using GitHub Secrets (for automated emails)**
1. Go to: https://github.com/YOUR_USERNAME/meal-planner/settings/secrets/actions
2. Click "New repository secret"
3. Name: `READWISE_API_TOKEN`
4. Value: Your token from step 1
5. Click "Add secret"

### 3. Enable Auto-Sync

Already enabled by default! Check `scripts/config.py`:

```python
ENABLE_READWISE_SYNC = True  # ✓ Already set
```

### 4. Test It

**CLI rating:**
```bash
python3 scripts/rate.py
# Rate an item as 🔖 Save
# You'll see: "✅ Saved to Readwise: Article Title..."
```

**Email rating:**
```bash
# Start rating server
python3 scripts/rating_server.py

# Click 🔖 Save button in email
# Article appears in Readwise Reader!
```

**Check Readwise:**
1. Visit: https://readwise.io/read/list
2. Your saved article should be in the inbox
3. Tagged with "Cultural Brief"

## How It Works

### Automatic Sync
When you save an item (via CLI or email), the system:
1. Saves rating to `data/feedback.json` ✓
2. Calls Readwise Reader API ✓
3. Sends: URL, title, source, summary (hook)
4. Article appears in Readwise inbox instantly

### What Gets Synced
- **URL** — Direct link to article
- **Title** — Article headline
- **Author** — Source name (e.g., "Arts & Letters Daily")
- **Summary** — The hook/description from your brief
- **Tag** — "Cultural Brief" (for filtering in Readwise)
- **Location** — Internal ID for tracking

### Non-Blocking
If Readwise sync fails (network issue, API down, etc.):
- ✅ Rating still saves to `feedback.json`
- ⚠️ Warning message shown
- 💪 You can manually re-sync later

## Manual Sync

### Sync All Previously Saved Items

If you enabled Readwise after already saving items:

```bash
python3 scripts/readwise_sync.py --sync-all
```

This will:
1. Load all saved items from `feedback.json`
2. Find corresponding articles from briefs
3. Send each to Readwise Reader
4. Show success/failure count

### Sync Specific Date Range

```bash
# Not yet implemented, but easy to add if needed
# python3 scripts/readwise_sync.py --from 2026-02-01 --to 2026-02-15
```

## Troubleshooting

### "Readwise API token not found"

**Fix:** Add token to .env or GitHub secrets (see Setup step 2)

```bash
# Check if token is set
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✓ Token set' if os.getenv('READWISE_API_TOKEN') else '✗ Token missing')"
```

### "Readwise authentication failed"

**Causes:**
- Token is incorrect (double-check copy/paste)
- Token expired (regenerate at https://readwise.io/access_token)
- Readwise account suspended

**Fix:**
1. Visit: https://readwise.io/access_token
2. Copy new token
3. Update .env or GitHub secret
4. Try again

### "Invalid request to Readwise"

**Common causes:**
- URL is malformed (rare — brief URLs are pre-validated)
- Title contains special characters (automatically handled)
- Duplicate article (Readwise accepts, but may merge)

**Fix:** Check the error message for details. Usually auto-recoverable.

### Articles Not Appearing in Readwise

**Check:**
1. Token is correct: Visit https://readwise.io/access_token
2. Sync is enabled: Check `scripts/config.py` → `ENABLE_READWISE_SYNC = True`
3. Item was actually saved: Check `data/feedback.json` for rating="save"
4. Readwise inbox: https://readwise.io/read/list (not archive)

**Manual test:**
```bash
python3 -c "from readwise_sync import save_to_readwise; save_to_readwise('https://example.com', 'Test Article')"
```

If this succeeds, integration is working!

### Disable Readwise Sync

If you want to temporarily disable:

```python
# In scripts/config.py
ENABLE_READWISE_SYNC = False
```

Saved items will still go to `feedback.json`, just not to Readwise.

## Advanced Usage

### Custom Tags in Readwise

Want to tag articles differently? Modify `scripts/readwise_sync.py`:

```python
payload = {
    "url": url,
    "title": title,
    "saved_using": "Cultural Brief",  # ← Change this
    # Or add: "tags": ["reading", "culture", "longform"]
}
```

### Highlight Integration

After reading in Readwise, your highlights sync back to Readwise.io:
1. Read article in Readwise Reader
2. Highlight passages
3. Export highlights to Obsidian/Notion/Roam
4. Use for research, writing, personal knowledge base

### Reading Stats

Check your reading patterns across services:
- **Cultural Brief stats**: `python3 scripts/taste_trends.py`
- **Readwise dashboard**: https://readwise.io/dashboard
- **Combined view**: Export Readwise data and join with `feedback.json`

## Privacy & Data

### What's Sent to Readwise
- Article URL (public web link)
- Article title (from RSS feed)
- Source name (e.g., "Arts & Letters Daily")
- Brief description/hook
- Tag: "Cultural Brief"

### What's NOT Sent
- Your ratings (👍/👎) — only saved items
- Click-through data
- Your email address (Readwise already has it from your account)
- Any other feedback.json data

### Readwise's Privacy
- Read their privacy policy: https://readwise.io/privacy
- Data stored securely on Readwise servers
- Used for sync across devices, email digests, exports
- You can delete your account anytime

## See Also

- [Readwise Reader Help](https://readwise.io/reader_doc)
- [Readwise API Documentation](https://readwise.io/api_deets)
- [One-Click Email Ratings](ONE_CLICK_RATINGS.md)
- [Reading Queue](../scripts/reading_queue.py)

Enjoy your enhanced reading workflow! 📚✨
