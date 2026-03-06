# Railway Deployment Guide

Deploy your Cultural Brief rating server to Railway so you can rate items from any device (phone, tablet, computer).

## Why Railway?

- ✅ **Free tier** - 500 hours/month, $5 credit
- ✅ **Works everywhere** - Rate from your phone!
- ✅ **Auto-deploy** - Push to GitHub → auto-updates
- ✅ **5-minute setup** - Dead simple
- ✅ **Built-in SSL** - Secure HTTPS automatically

## Setup (5 minutes)

### Step 1: Sign Up for Railway

1. Go to: https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your GitHub

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository: `yashodercoder/meal-planner`
4. Railway will detect your project automatically

### Step 3: Configure Environment Variables

In your Railway project dashboard:

1. Go to "Variables" tab
2. Add these variables:

```
FEEDBACK_PATH=/app/cultural-brief/data/feedback.json
READWISE_API_TOKEN=OHweiD2M5nU2uw0YeNN2X6BTRu1Tn9N0t89aEGFJhG37dKwMEqfAbYCXmtNxC8puMlOrNEs01L3RVmI1sNoW6r9qcLdoiHhlkwoOLMhmie457ItZy6r92Db6zBrPNaRDKfUFhvHkIKtdQhohmmmswJ7y4udTw8C3mOFFwfptgfiiu2Fcf7Ho1wJy1DO9XgmsBDe7w1UP
```

**Note:** Railway automatically sets `PORT` - don't add it manually.

### Step 4: Get Your Public URL

1. Go to "Settings" tab
2. Scroll to "Domains"
3. Click "Generate Domain"
4. Copy your URL (looks like: `your-app.up.railway.app`)

Example: `https://meal-planner-production-a1b2.up.railway.app`

### Step 5: Update GitHub Secrets

Add your Railway URL to GitHub so emails use it:

1. Go to: https://github.com/yashodercoder/meal-planner/settings/secrets/actions
2. Click "New repository secret"
3. Name: `RATING_SERVER_URL`
4. Value: Your Railway URL (e.g., `https://your-app.up.railway.app`)
5. Click "Add secret"

### Step 6: Trigger Deployment

Railway should deploy automatically, but if not:

1. Go to "Deployments" tab
2. Click "Deploy" or push a commit to GitHub
3. Wait ~2 minutes for build to complete
4. Check logs to verify it's running

### Step 7: Test It!

1. Visit your Railway URL in browser
2. You should see: "📚 Cultural Brief Rating Server"
3. Tomorrow's email will have working rating buttons!

Or test now:
```bash
cd /tmp/meal-planner/cultural-brief
RATING_SERVER_URL=https://your-app.up.railway.app python3 scripts/deliver.py
```

## Verify It's Working

**Check server is up:**
```bash
curl https://your-app.up.railway.app/
# Should return HTML with "Cultural Brief Rating Server"
```

**Test a rating:**
```bash
curl "https://your-app.up.railway.app/rate?item_id=test123&rating=up&date=2026-02-20&source=Test&title=Test+Article"
# Should return HTML confirmation page
```

**Check logs in Railway:**
1. Go to Railway dashboard
2. Click your project
3. "Deployments" tab → Latest deployment → "View Logs"
4. You should see: "Server running on 0.0.0.0:XXXX"

## Important Notes

### Data Persistence

⚠️ **Railway's filesystem is ephemeral** - when the server restarts, `feedback.json` is lost!

**Solution:** We need to modify the rating server to store ratings in a database instead. Options:

**Option 1: Use Railway's PostgreSQL** (recommended)
- Add Postgres to your Railway project
- Store ratings in database table
- Survives server restarts

**Option 2: Use GitHub as storage**
- Rating server commits to GitHub via API
- Each rating creates a git commit
- Persists forever, fully backed up

**Option 3: Use Railway's volume mounts** (in beta)
- Mount persistent storage
- Keeps feedback.json across restarts

For now, **the server works but ratings might be lost on restart**. I'll implement database storage next.

### Auto-Deploy

Every time you push to GitHub, Railway automatically deploys:
- Edit code → `git push` → Railway rebuilds → Live in ~2 min

### Free Tier Limits

- **500 hours/month** - Enough for always-on server
- **$5 credit** - Plenty for this app
- **1GB RAM** - More than enough
- **1GB storage** - Plenty for logs

If you exceed limits, Railway will email you. Upgrade is $5/month.

### SSL/HTTPS

Railway provides free SSL certificates automatically. Your rating URLs are:
- ✅ `https://your-app.railway.app` (secure)
- ❌ `http://your-app.railway.app` (redirects to HTTPS)

## Troubleshooting

### "Application failed to respond"

**Check logs:**
1. Railway dashboard → Deployments → View Logs
2. Look for errors in Python startup

**Common causes:**
- Missing environment variable
- Port binding issue (should use `0.0.0.0`)
- Import error (missing package)

**Fix:**
- Verify all env vars are set
- Check `requirements.txt` is complete
- Redeploy from Railway dashboard

### "Cannot find module"

**Cause:** Missing Python package

**Fix:**
1. Add package to `cultural-brief/requirements.txt`
2. Push to GitHub
3. Railway auto-redeploys

### Ratings not saving

**Check:**
1. Railway logs show "Rating saved"?
2. Is `FEEDBACK_PATH` set correctly?
3. Does directory exist? (Railway might need `mkdir -p`)

**Temporary fix:**
```python
# In rating_server.py, ensure directory exists:
FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
```

### Server keeps restarting

**Check logs for crash errors:**
- Python exceptions?
- Port already in use? (shouldn't happen on Railway)
- Out of memory? (very unlikely for this app)

**Railway auto-restarts** on crashes (up to 10 times), then gives up.

## Next Steps

### Add Database Storage (Recommended)

To persist ratings across server restarts:

1. **Add PostgreSQL:**
   - Railway dashboard → "New" → "Database" → "PostgreSQL"
   - Railway sets `DATABASE_URL` automatically

2. **Update rating_server.py:**
   - Use `psycopg2` to store ratings in Postgres
   - Schema: `ratings` table with columns for date, item_id, rating, clicked

3. **Migrate existing data:**
   - One-time script to load `feedback.json` into database

### Custom Domain (Optional)

Want `ratings.yourdomain.com` instead of Railway subdomain?

1. Railway dashboard → Settings → Domains
2. Click "Custom Domain"
3. Enter your domain (e.g., `ratings.yourdomain.com`)
4. Add CNAME record in your DNS: `ratings CNAME your-app.up.railway.app`
5. Railway provisions SSL certificate automatically

### Monitoring

**Railway built-in:**
- Deployments → Click deployment → View Logs
- Metrics tab shows CPU/RAM usage

**External monitoring:**
- Add UptimeRobot to ping your server every 5 minutes
- Get alerts if server goes down

## Costs

**Free tier:**
- $5 credit per month
- 500 execution hours
- 100GB bandwidth

**This app uses:**
- ~730 hours/month (always-on)
- <1GB bandwidth (very few requests)
- ~100MB RAM

**Estimated cost:** $0-5/month (well within free tier)

If you exceed, Railway emails you before charging.

## Security

**What's exposed:**
- `/` - Public landing page (harmless)
- `/rate` - Rating endpoint (needs valid parameters)

**What's protected:**
- Readwise token is environment variable (not in code)
- No user authentication needed (ratings are personal)
- HTTPS encrypts all traffic

**Recommendations:**
- Don't share your Railway URL publicly
- Rating links in email are effectively "secret URLs"
- Consider adding a simple API key if you're worried

## Alternative: Render.com

If Railway doesn't work, try Render (very similar):

1. Sign up: https://render.com
2. "New Web Service"
3. Connect GitHub repo
4. Build: `pip install -r cultural-brief/requirements.txt`
5. Start: `cd cultural-brief && python3 scripts/rating_server.py`
6. Add environment variables
7. Deploy!

Render's free tier: 750 hours/month (also plenty)

## See Also

- [One-Click Email Ratings](ONE_CLICK_RATINGS.md)
- [Readwise Integration](READWISE_INTEGRATION.md)
- Railway docs: https://docs.railway.app

Happy rating from anywhere! 📱✨
