"""
Tims Picks SMS Sender
---------------------
Fetches today's top NHL picks via Claude AI and sends them
as a text message via Twilio.

Run manually:  python tims_picks_sms.py
Schedule it:   See README for cron / GitHub Actions setup.
"""

import os
import re
import json
import datetime
import anthropic
from twilio.rest import Client

# ── CONFIG ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY",  "YOUR_ANTHROPIC_API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.environ.get("TWILIO_AUTH_TOKEN",  "")
TWILIO_FROM        = os.environ.get("TWILIO_FROM",        "+15705725835")
TWILIO_TO          = os.environ.get("TWILIO_TO",          "+14164546850")
# ─────────────────────────────────────────────────────────────────────────────

TODAY = datetime.date.today().strftime("%B %d, %Y")


def fetch_picks_json() -> dict | None:
    """
    First attempt: ask Claude to return structured JSON picks.
    Returns a dict on success, None if parsing fails.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Today is {TODAY}. Search for today's NHL games and identify the best goal scorer picks for the Tim Hortons Hockey Challenge.

Use sites like DailyFaceoff.com, Dobber Hockey, or any NHL stats source to find today's games and top forwards.

You MUST respond with ONLY a raw JSON object. Do not include any explanation, apology, or text outside the JSON. Do not use markdown or code fences. Start your response with {{ and end with }}.

Use this exact structure:
{{
  "date": "{TODAY}",
  "top3": [
    {{"rank": 1, "name": "First Last", "team": "ABC", "opponent": "vs XYZ", "goal_prob": "40%", "reason": "Top line, strong matchup"}},
    {{"rank": 2, "name": "First Last", "team": "ABC", "opponent": "vs XYZ", "goal_prob": "36%", "reason": "PP1, hot streak"}},
    {{"rank": 3, "name": "First Last", "team": "ABC", "opponent": "vs XYZ", "goal_prob": "33%", "reason": "High-scoring team tonight"}}
  ],
  "best_matchup": {{"name": "First Last", "team": "ABC", "opponent": "vs XYZ", "reason": "Facing weak goalie"}},
  "sleeper": {{"name": "First Last", "team": "ABC", "opponent": "vs XYZ", "reason": "Under the radar value pick"}},
  "summary": "One sentence about today's NHL slate."
}}

Use real player names from today's actual NHL schedule. If you are unsure of exact probabilities, estimate based on line placement and matchup quality."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    raw = "".join(b.text for b in response.content if hasattr(b, "text")).strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    print(f"[DEBUG] Raw response:\n{raw[:500]}\n")

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON block
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None  # Parsing failed


def fetch_picks_text() -> str:
    """
    Fallback: ask Claude for picks as plain text if JSON fails.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Today is {TODAY}. Search for today's NHL games and give me the top 3 goal scorer picks for the Tim Hortons Hockey Challenge.

Format your response as a short, clean text message like this example:

🏒 TIMS PICKS — March 4, 2026

🎯 TOP 3 PICKS:
1. Auston Matthews (TOR) vs BUF — 44% goal prob. Top line, PP1.
2. Leon Draisaitl (EDM) vs CGY — 41% goal prob. Elite scorer, rivalry game.
3. David Pastrnak (BOS) vs MTL — 38% goal prob. Hot streak, weak goalie.

📈 BEST MATCHUP: Nathan MacKinnon (COL) vs ARI — faces backup goalie.
😴 SLEEPER: Brock Boeser (VAN) vs SEA — sneaky value on PP1.

📊 Strong 7-game slate tonight with several high-scoring matchups.

Good luck! ☕

Use real player names from today's actual schedule."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=600,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    return "".join(b.text for b in response.content if hasattr(b, "text")).strip()


def build_sms_from_json(picks: dict) -> str:
    lines = [f"🏒 TIMS PICKS — {picks.get('date', TODAY)}", ""]

    top3 = picks.get("top3", [])
    if top3:
        lines.append("🎯 TOP 3 PICKS:")
        for p in top3:
            lines.append(f"  {p.get('rank','')}. {p.get('name','?')} ({p.get('team','')}) {p.get('opponent','')} — {p.get('goal_prob','')}")
            if p.get('reason'):
                lines.append(f"     {p['reason']}")

    bm = picks.get("best_matchup")
    if bm:
        if isinstance(bm, list): bm = bm[0]
        lines.append("")
        lines.append(f"📈 BEST MATCHUP: {bm.get('name','?')} ({bm.get('team','')}) {bm.get('opponent','')}")
        if bm.get('reason'): lines.append(f"   {bm['reason']}")

    sl = picks.get("sleeper")
    if sl:
        if isinstance(sl, list): sl = sl[0]
        lines.append(f"😴 SLEEPER: {sl.get('name','?')} ({sl.get('team','')}) {sl.get('opponent','')}")
        if sl.get('reason'): lines.append(f"   {sl['reason']}")

    if picks.get("summary"):
        lines.append("")
        lines.append(f"📊 {picks['summary']}")

    lines.extend(["", "Good luck! ☕"])
    return "\n".join(lines)


def send_sms(body: str) -> str:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(body=body, from_=TWILIO_FROM, to=TWILIO_TO)
    return message.sid


def main():
    print(f"⏳ Fetching picks for {TODAY}...")

    # Try JSON first
    picks_json = fetch_picks_json()

    if picks_json:
        print("✅ Got structured picks.")
        sms_body = build_sms_from_json(picks_json)
    else:
        print("⚠️  JSON parse failed, falling back to plain text picks...")
        sms_body = fetch_picks_text()

    print("\n── SMS PREVIEW ──────────────────────────")
    print(sms_body)
    print("─────────────────────────────────────────\n")

    sid = send_sms(sms_body)
    print(f"✅ SMS sent! Twilio SID: {sid}")


if __name__ == "__main__":
    main()
