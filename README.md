# Cultural Brief

Daily email of 5 curated cultural items (books, essays, criticism, podcasts) filtered by Claude Haiku against a taste profile.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file for local testing:

```bash
cp .env.example .env
```

Edit `.env` and add:

```
ANTHROPIC_API_KEY=sk-ant-...
RESEND_API_KEY=re_...
BRIEF_TO=your-email@example.com
BRIEF_FROM=brief@yourdomain.com  # optional, defaults to onboarding@resend.dev
```

### 3. Configure GitHub Secrets

For automated daily emails, add these secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:
   - `ANTHROPIC_API_KEY` — Your Claude API key from console.anthropic.com
   - `RESEND_API_KEY` — Your Resend API key from resend.com
   - `BRIEF_TO` — Email address to receive the daily brief
   - `BRIEF_FROM` — (optional) Verified sender email address

## Testing Locally

Run the full pipeline manually:

```bash
# 1. Fetch RSS feeds
python3 scripts/fetch.py

# 2. Filter with Claude
python3 scripts/filter.py

# 3. Send email (or preview in terminal)
python3 scripts/deliver.py

# 4. Rate items (CLI)
python3 scripts/rate.py
```

## Testing in GitHub Actions

Before enabling the daily schedule, test the workflow manually:

1. Go to **Actions** tab in GitHub
2. Select **Cultural Brief** workflow
3. Click **Run workflow** → **Run workflow**
4. Check the logs for any errors
5. Verify you received the email

## Failure Notifications

If the workflow fails (RSS fetch error, API timeout, etc.), you'll receive an email notification at the address specified in `BRIEF_TO`.

The notification includes:
- Which step failed
- Date and time of failure
- Link to GitHub Actions logs

## Cost Estimates

- **Claude Haiku**: ~$0.30/month (one call per day, ~4k tokens/call)
- **Resend**: Free tier (100 emails/day)
- **GitHub Actions**: Free tier (2,000 minutes/month)

## Workflow Schedule

The workflow runs daily at **6:00 AM UTC**. To change the schedule, edit `.github/workflows/cultural-brief.yml`:

```yaml
on:
  schedule:
    - cron: "0 6 * * *"   # Change time here
```

## File Structure

```
cultural-brief/
├── sources.yaml            # RSS feed URLs
├── taste_profile.md        # Taste criteria for filtering
├── scripts/
│   ├── fetch.py            # Fetch RSS feeds
│   ├── filter.py           # Filter with Claude Haiku
│   ├── deliver.py          # Send email via Resend
│   ├── rate.py             # CLI rating interface
│   └── notify_failure.py   # Send failure notifications
├── data/
│   ├── feedback.json       # Rating history
│   └── briefs/             # Archived daily briefs (YYYY-MM-DD.json)
└── .github/workflows/
    └── cultural-brief.yml  # Daily automation
```

## Troubleshooting

### No items fetched
- Check that RSS feed URLs in `sources.yaml` are valid
- Test individual feeds: `curl -I <feed-url>`
- Some feeds may be rate-limited or require authentication

### Email not delivered
- Verify `RESEND_API_KEY` is set correctly
- Check sender domain is verified in Resend dashboard
- Review Resend logs at resend.com/logs

### Claude API errors
- Verify `ANTHROPIC_API_KEY` is valid
- Check API quota at console.anthropic.com
- Review error message in failure notification email

### GitHub Actions permission errors
- Ensure workflow has `contents: write` permission
- Check that Actions are enabled in repository settings
