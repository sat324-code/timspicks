import os
import re
import time
import anthropic
from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Config ────────────────────────────────────────────────────────────────────
URL = "https://hockeychallengehelper.com"

ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
TWILIO_ACCOUNT_SID  = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN   = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM         = os.environ["TWILIO_FROM"]
TWILIO_TO           = os.environ["TWILIO_TO"]

# ── Scrape with headless Chrome ───────────────────────────────────────────────
def fetch_rendered_page(url: str) -> str:
    """Use headless Chrome to fully render the JS page before extracting text."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        # Wait up to 15s for a table to appear (the picks are in a table)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        time.sleep(3)  # extra buffer for dynamic content to settle
        page_text = driver.find_element(By.TAG_NAME, "body").text
    except Exception as e:
        print(f"Warning during page load: {e}")
        page_text = driver.find_element(By.TAG_NAME, "body").text
    finally:
        driver.quit()

    return page_text

# ── Summarise with Claude ─────────────────────────────────────────────────────
def get_picks_summary(page_text: str) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
You are an NHL picks assistant analyzing data from hockeychallengehelper.com.

The page contains 3 separate pick tables labeled "Pick #1", "Pick #2", and "Pick #3".
Each table lists multiple players with their stats including goal-scoring odds/probability.

Your task:
- From the "Pick #1" table: select the ONE player with the best odds of scoring a goal
- From the "Pick #2" table: select the ONE player with the best odds of scoring a goal  
- From the "Pick #3" table: select the ONE player with the best odds of scoring a goal

Rules:
- TOTAL message must be 300 characters or less (strict hard limit)
- Format EXACTLY like this:
  🏒 Tim's Picks:
  P1: Laine(CBJ) 3.2pts
  P2: Aho(CAR) 2.8pts
  P3: Hellebuyck(WPG) 2.1pts
- Include pick number prefix (P1/P2/P3), player name, (TEAM abbreviation), and projected points
- Round projected points to 1 decimal place
- Output ONLY the formatted picks, nothing else

Page text:
{page_text[:8000]}
"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()

# ── Send SMS ──────────────────────────────────────────────────────────────────
def send_sms(body: str) -> None:
    if len(body) > 300:
        body = body[:300]
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = twilio_client.messages.create(
        body=body,
        from_=TWILIO_FROM,
        to=TWILIO_TO,
    )
    print(f"SMS sent — SID: {message.sid}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Fetching (headless Chrome): {URL} …")
    page_text = fetch_rendered_page(URL)
    print(f"Page text length: {len(page_text)} chars")
    print(f"Page preview:\n{page_text[:500]}\n")

    print("Asking Claude for top picks …")
    summary = get_picks_summary(page_text)
    print(f"Summary ({len(summary)} chars):\n{summary}")

    print("Sending SMS …")
    send_sms(summary)

if __name__ == "__main__":
    main()
