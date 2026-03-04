"""
Tims Picks SMS Sender
---------------------
Fetches today's top NHL picks via Claude AI and sends them
as a text message via Twilio.

Run manually:  python tims_picks_sms.py
Schedule it:   See README below for cron / GitHub Actions setup.
"""

import os
import json
import datetime
import anthropic
from twilio.rest import Client

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "AC221c87662d7bb3038492bc4f1232a29e")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN",  "594b06bfbc03f3c44186aa664f55be61")
TWILIO_FROM        = os.environ.get("TWILIO_FROM",        "+15705725835")   # your Twilio number
TWILIO_TO          = os.environ.get("TWILIO_TO",          "+14164546850")   # your personal number
# ─────────────────────────────────────────────────────────────────────────────


def fetch_picks() -> dict:
    """Ask Claude (with web search) for today's top Tims picks, returned as JSON."""
    today = datetime.date.today().strftime("%B %d, %Y")

    prompt = f"""Today is {today}.

Search for today's top NHL goal scorer picks for the Tim Hortons Hockey Challenge (Tims Picks).
Look at sites like 5v5hockey.com, DailyFaceoff, Dobber Hockey, or any reliable NHL analytics source.

Return ONLY a valid JSON object — no markdown, no backticks, no extra text — with this structure:

{{
  "date": "{today}",
  "top3": [
    {{"rank": 1, "name": "Player Name", "team": "TEAM", "opponent": "vs OPP", "goal_prob": "42%", "reason": "Short reason"}},
    {{"rank": 2, "name": "Player Name", "team": "TEAM", "opponent": "vs OPP", "goal_prob": "38%", "reason": "Short reason"}},
    {{"rank": 3, "name": "Player Name", "team": "TEAM", "opponent": "vs OPP", "goal_prob": "35%", "reason": "Short reason"}}
  ],
  "best_matchup": {{"name": "Player Name", "team": "TEAM", "opponent": "vs OPP", "reason": "Short reason"}},
  "sleeper":      {{"name": "Player Name", "team": "TEAM", "opponent": "vs OPP", "reason": "Short reason"}},
  "summary": "One sentence overview of today's slate."
}}
"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    raw = "".join(b.text for b in response.content if hasattr(b, "text")).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON from response:\n{raw}")


def build_sms(picks: dict) -> str:
    """Format picks data into a concise SMS message."""
    lines = []
    lines.append(f"🏒 TIMS PICKS — {picks.get('date', 'Today')}")
    lines.append("")

    lines.append("🎯 TOP 3 PICKS:")
    for p in picks.get("top3", []):
        lines.append(f"  {p['rank']}. {p['name']} ({p['team']}) {p['opponent']} — {p.get('goal_prob','')}")

    bm = picks.get("best_matchup")
    if bm:
        lines.append("")
        lines.append(f"📈 BEST MATCHUP: {bm['name']} ({bm['team']}) {bm['opponent']}")

    sl = picks.get("sleeper")
    if sl:
        lines.append(f"😴 SLEEPER: {sl['name']} ({sl['team']}) {sl['opponent']}")

    summary = picks.get("summary")
    if summary:
        lines.append("")
        lines.append(f"📊 {summary}")

    lines.append("")
    lines.append("Good luck! ☕")
    return "\n".join(lines)


def send_sms(body: str) -> str:
    """Send the SMS via Twilio and return the message SID."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=body,
        from_=TWILIO_FROM,
        to=TWILIO_TO
    )
    return message.sid


def main():
    print("⏳ Fetching today's picks...")
    picks = fetch_picks()
    print("✅ Picks fetched.")

    sms_body = build_sms(picks)
    print("\n── SMS PREVIEW ──────────────────────────")
    print(sms_body)
    print("─────────────────────────────────────────\n")

    sid = send_sms(sms_body)
    print(f"✅ SMS sent! Twilio SID: {sid}")


if __name__ == "__main__":
    main()
