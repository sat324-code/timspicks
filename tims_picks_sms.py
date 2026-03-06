import os
import re
import anthropic
from twilio.rest import Client
from urllib.request import urlopen, Request
from urllib.error import URLError

# ── Config ────────────────────────────────────────────────────────────────────
URL = "https://hockeychallengehelper.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TimsPicksBot/1.0)"}

ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
TWILIO_ACCOUNT_SID  = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN   = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM         = os.environ["TWILIO_FROM"]
TWILIO_TO           = os.environ["TWILIO_TO"]

# ── Scrape ────────────────────────────────────────────────────────────────────
def fetch_page(url: str) -> str:
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def strip_tags(html: str) -> str:
    """Very lightweight tag stripper — no external deps needed."""
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.S)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

# ── Summarise with Claude ─────────────────────────────────────────────────────
def get_picks_summary(page_text: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
You are an NHL daily-picks assistant. Below is the raw text scraped from
hockeychallengehelper.com. Your job:

1. Identify today's top recommended player picks (typically skaters and goalies
   for the NHL Daily Challenge or similar contest).
2. For each pick include: player name, team, and why they are recommended
   (e.g. matchup, points/goals pace, power-play time, etc.).
3. Keep the total SMS message under 320 characters so it fits in 2 texts.
4. Format as:
   🏒 Tim's Picks – <date>
   • <Player>, <Team> – <short reason>
   • ...
   Good luck!

Raw page text (first 8000 chars):
{page_text[:8000]}
"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()

# ── Send SMS ──────────────────────────────────────────────────────────────────
def send_sms(body: str) -> None:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = twilio_client.messages.create(
        body=body,
        from_=TWILIO_FROM,
        to=TWILIO_TO,
    )
    print(f"SMS sent — SID: {message.sid}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Fetching {URL} …")
    html = fetch_page(URL)
    page_text = strip_tags(html)
    print(f"Page text length: {len(page_text)} chars")

    print("Asking Claude for top picks …")
    summary = get_picks_summary(page_text)
    print(f"Summary:\n{summary}")

    print("Sending SMS …")
    send_sms(summary)

if __name__ == "__main__":
    main()
