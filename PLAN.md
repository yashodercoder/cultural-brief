# Cultural Brief — Build Plan

## What we're building

Daily email of 5 curated cultural items (books, essays, criticism, podcasts) filtered by Claude Haiku against a taste profile. Simple per-item rating via CLI after reading.

## What's cut from the spec

- Weekly digest (Sonnet) — add later
- Learning engine + monthly taste reports — add later
- Save consumption tracking — dropped
- Email feedback webhook — too much infrastructure; CLI only
- YouTube/podcast sources — add later; RSS only for now
- Numeric scoring — dropped; Haiku just selects + writes hooks

## Repo structure

```
cultural-brief/
├── sources.yaml            # RSS feed URLs
├── taste_profile.md        # Compressed taste criteria (~150 tokens)
├── scripts/
│   ├── fetch.py            # feedparser → raw items JSON
│   ├── filter.py           # single Haiku call → 5 items + one-line hooks
│   ├── deliver.py          # format + send via Resend
│   └── rate.py             # CLI: show today's brief, prompt 👍 👎 🔖 per item
├── data/
│   ├── feedback.json       # append-only rating log
│   └── briefs/             # archived daily briefs (YYYY-MM-DD.json)
├── requirements.txt
└── .github/workflows/daily.yml
```

## Rating system (simple)

`rate.py` reads today's brief from `data/briefs/` and loops through each item:

```
[1/5] "The Empathy Trap" — The Atlantic
      Why: Selin Çalışkan on how emotional labor warps women's sense of self.
      Rate: (u)p / (d)own / (s)ave / (skip) »
```

Writes to `feedback.json`:
```json
[
  {
    "date": "2026-02-18",
    "item_id": "abc123",
    "title": "The Empathy Trap",
    "source": "The Atlantic",
    "rating": "up"
  }
]
```

No analysis of feedback yet — just accumulate it cleanly.

## GitHub Actions (daily.yml)

Single job, three steps:
1. `fetch.py` — pull RSS feeds, write raw items
2. `filter.py` — Haiku call, write today's brief to `data/briefs/YYYY-MM-DD.json`
3. `deliver.py` — send email via Resend

`rate.py` runs locally (not in CI).

## Build order

1. `sources.yaml` + `taste_profile.md`
2. `fetch.py` — feedparser, confirm items arrive
3. `filter.py` — single Haiku batch call
4. `deliver.py` — Resend email, plain format
5. `.github/workflows/daily.yml` — cron at 6am
6. `rate.py` — CLI rating, feedback.json

## Estimated cost

- Claude Haiku: ~$0.30/month (one call/day, ~4k tokens/call)
- Resend: free tier
- GitHub Actions: free tier
