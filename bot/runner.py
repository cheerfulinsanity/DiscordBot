import os
import requests

TOKEN = os.getenv("TOKEN")
STEAM_ID = 84228471  # Replace or keep as is for your test

QUERY = """
query GetMatch($steamId: Long!) {
  player(steamAccountId: $steamId) {
    matches(request: {take: 1}) {
      id
      durationSeconds
      startDateTime
      players {
        steamAccountId
        isVictory
        hero { name }
        kills
        deaths
        assists
      }
    }
  }
}
"""

def fetch_latest_match(steam_id):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "STRATZ_API"
    }
    payload = {
        "query": QUERY,
        "variables": { "steamId": steam_id }
    }

    print(f"🔍 Fetching latest match for SteamID {steam_id}...")
    res = requests.post("https://api.stratz.com/graphql", headers=headers, json=payload)
    if res.status_code != 200:
        print(f"❌ HTTP error {res.status_code}: {res.text}")
        return

    try:
        data = res.json()
        match = data["data"]["player"]["matches"][0]
        print(f"✅ Match ID: {match['id']} — Duration: {match['durationSeconds']} seconds")

        for p in match["players"]:
            if p["steamAccountId"] == steam_id:
                win_str = "🏆 Win" if p["isVictory"] else "💀 Loss"
                print(f"🧙 {p['hero']['name']}: {p['kills']}/{p['deaths']}/{p['assists']} — {win_str}")
                return
        print("❌ Could not find player in match.")
    except Exception as e:
        print(f"❌ JSON parsing error or missing data: {e}")
        print("Response text:", res.text)

def run_bot():
    if not TOKEN:
        print("❌ TOKEN environment variable is not set.")
        return

    fetch_latest_match(STEAM_ID)
    print("✅ run_bot() finished without crashing")

if __name__ == "__main__":
    run_bot()
