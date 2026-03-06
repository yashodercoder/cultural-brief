# Source Discovery

Automatically discover new publications and RSS sources that match your taste profile.

## How It Works

The source discovery system uses Claude AI to:
1. **Analyze** your taste profile
2. **Review** sources you've rated highly
3. **Search** for similar publications
4. **Validate** RSS feeds are working
5. **Suggest** 10 new sources monthly

All automatically via GitHub Actions!

## Manual Discovery

Run source discovery anytime:

```bash
cd cultural-brief
python3 scripts/discover_sources.py
```

**Options:**
```bash
# Discover 20 sources instead of 10
python3 scripts/discover_sources.py --count 20

# Auto-add validated sources to sources.yaml
python3 scripts/discover_sources.py --auto-add

# Skip RSS validation (faster, but may add broken feeds)
python3 scripts/discover_sources.py --skip-validation
```

## Automated Monthly Discovery

A GitHub Action runs on the **1st of every month** at 10:00 AM UTC:

1. Discovers 10 new sources
2. Validates RSS feeds
3. Creates a Pull Request with the additions
4. You review and merge (or close) the PR

**Manual trigger:**
1. Go to: https://github.com/YOUR_USERNAME/meal-planner/actions
2. Click "Monthly Source Discovery"
3. Click "Run workflow"

## What Gets Discovered

Claude looks for:
- **Literary magazines** (like Paris Review, Granta)
- **Film/TV criticism** (like Film Comment, Vulture)
- **Essay platforms** (like Aeon, Real Life)
- **Academic publications** (like Public Books, Boston Review)
- **Quality Substacks** (active critics and writers)
- **International sources** (LRB, TLS, Dublin Review)

Prioritizes sources similar to your **top-rated** publications.

## Review Process

When you get a source discovery PR:

### 1. Check the Suggestions

Look at the diff in `sources.yaml` - do they match your taste?

### 2. Test the Feeds

```bash
cd cultural-brief
python3 scripts/fetch.py
```

This fetches from all sources (including new ones) and shows what content you'd get.

### 3. Merge or Close

- **Merge** if you like the sources → they'll appear in tomorrow's brief
- **Close** if not a good fit → no problem, next month will try again

## Customization

### Adjust Discovery Frequency

Edit `.github/workflows/discover-sources.yml`:

```yaml
schedule:
  # Weekly on Mondays:
  - cron: '0 10 * * 1'

  # Bi-weekly (1st and 15th):
  - cron: '0 10 1,15 * *'

  # Quarterly (Jan, Apr, Jul, Oct):
  - cron: '0 10 1 1,4,7,10 *'
```

### Adjust Discovery Count

Change from 10 to 20 sources per discovery:

```yaml
- name: Discover new sources
  run: |
    python3 scripts/discover_sources.py --count 20 --auto-add
```

### Add Manual Filters

Edit `scripts/discover_sources.py` to add constraints:

```python
# Only discover from specific categories
categories = ["literary", "film", "academic"]

# Exclude certain types
exclude_keywords = ["celebrity", "gossip", "news"]

# Prioritize international sources
prefer_international = True
```

## Discovery Algorithm

The discovery prompt considers:

1. **Taste Profile** - Your documented preferences
2. **Top-Rated Sources** - Publications you've given 👍
3. **Current Sources** - Avoids duplicates
4. **Variety** - Mixes categories and perspectives
5. **Quality** - Prioritizes prestige and active publications

## Troubleshooting

### "No sources discovered"

**Cause:** Claude couldn't find new sources, or all suggestions were duplicates

**Fix:**
- Run with `--count 20` to get more suggestions
- Update taste profile to be more specific
- Check current sources - you might already have everything!

### "All feeds failed validation"

**Cause:** Suggested feeds are broken or inactive

**Fix:**
- Claude sometimes suggests defunct publications
- Close the PR, next month will try again
- Manually add working feeds if you find them

### "Discovered sources don't match taste"

**Cause:** Algorithm needs tuning based on your ratings

**Fix:**
- Rate more items to train the system
- Update taste profile to be more explicit
- Manually add sources you discover on your own

### "Discovery action failed"

**Check logs:**
1. GitHub → Actions → Monthly Source Discovery
2. Click failed run → View logs
3. Look for Python errors

**Common issues:**
- ANTHROPIC_API_KEY not set in secrets
- Network timeout (Claude API)
- sources.yaml syntax error

## Manual Source Addition

Found a great source? Add it manually:

```yaml
# In sources.yaml:
rss:
  - name: Your New Source
    url: https://example.com/feed/
```

Then test:
```bash
python3 scripts/fetch.py
```

## Source Lifecycle

**Active sources** → Regularly appear in briefs
**Inactive sources** → Rarely post, but kept in rotation
**Broken sources** → Removed during next cleanup

Future enhancement: Auto-remove sources that haven't published in 90 days.

## See Also

- [Taste Profile](../taste_profile.md) - Your reading preferences
- [Source Diversity](../sources.yaml) - Current source list
- [Stats & Analytics](taste_trends.py) - See what you actually like

Happy discovering! 🔍✨
