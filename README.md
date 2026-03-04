# Tims Picks SMS — Setup Guide

Every morning this script fetches today's top NHL goal-scorer picks via Claude AI
and texts them to your phone using Twilio.

---

## Files

| File | Purpose |
|------|---------|
| `tims_picks_sms.py` | Main script — fetch picks + send SMS |
| `.github/workflows/tims_picks.yml` | GitHub Actions scheduler (runs daily at 8 AM ET) |

---

## Option A: GitHub Actions (Recommended — fully automated, free)

### Step 1 — Create a GitHub repo

1. Go to https://github.com/new
2. Create a **private** repo (e.g. `tims-picks`)
3. Upload `tims_picks_sms.py` to the root of the repo
4. Create the folder `.github/workflows/` and upload `tims_picks.yml` inside it

### Step 2 — Add your secrets

In your GitHub repo go to **Settings → Secrets and variables → Actions → New repository secret**
and add each of these:

| Secret Name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (https://console.anthropic.com) |
| `TWILIO_ACCOUNT_SID` | AC221c87662d7bb3038492bc4f1232a29e |
| `TWILIO_AUTH_TOKEN` | Your Twilio auth token |
| `TWILIO_FROM` | +15705725835 |
| `TWILIO_TO` | +14164546850 |

### Step 3 — Test it manually

In your GitHub repo go to **Actions → Tims Picks SMS → Run workflow**
You should get a text within about 30 seconds!

### Step 4 — Done!

The workflow runs automatically every morning at 8:00 AM ET.
You can change the time by editing the `cron` line in `tims_picks.yml`.

---

## Option B: Run locally on your computer

### Install dependencies
```bash
pip install anthropic twilio
```

### Set environment variables (Mac/Linux)
```bash
export ANTHROPIC_API_KEY="your_key_here"
export TWILIO_ACCOUNT_SID="AC221c87662d7bb3038492bc4f1232a29e"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_FROM="+15705725835"
export TWILIO_TO="+14164546850"
```

### Run manually
```bash
python tims_picks_sms.py
```

### Schedule with cron (Mac/Linux) — runs at 8 AM daily
```bash
crontab -e
# Add this line:
0 8 * * * cd /path/to/your/folder && python tims_picks_sms.py
```

---

## Getting your Anthropic API Key

1. Go to https://console.anthropic.com
2. Click **API Keys** in the left sidebar
3. Click **Create Key** and copy it

---

## Sample SMS you'll receive

```
🏒 TIMS PICKS — March 4, 2025

🎯 TOP 3 PICKS:
  1. Auston Matthews (TOR) vs BUF — 44%
  2. Leon Draisaitl (EDM) vs CGY — 41%
  3. David Pastrnak (BOS) vs MTL — 38%

📈 BEST MATCHUP: Nathan MacKinnon (COL) vs ARI
😴 SLEEPER: Brock Boeser (VAN) vs SEA

📊 Strong offensive slate tonight with 7 games on the schedule.

Good luck! ☕
```
