import requests
import os

TOKEN = os.getenv("TOKEN")

QUERY = """
query GetLatestMatch($steamId: Long!) {
  player(steamAccountId: $steamId) {
    matches(request: { take: 1 }) {
      id
      durationSeconds
      gameMode
      startDateTime
      players {
        steamAccountId
        isVictory
        hero { id name }
        kills
        deaths
        assists
        goldPerMinute
        experiencePerMinute
        numLastHits
      }
    }
  }
}
"""

def fetch_latest_match(steam_id: int, token=None) -> dict | None:
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "STRATZ_API"
    }

    payload = {
        "query": QUERY,
        "variables": {"steamId": steam_id}
    }

    res = requests.post("https://api.stratz.com/graphql", headers=headers, json=payload)
    if res.status_code != 200:
        print(f"❌ HTTP error {res.status_code}: {res.text}")
        return None

    try:
        data = res.json()
        match = data["data"]["player"]["matches"][0]
        match_id = match["id"]
        is_turbo = (match["gameMode"] == "TURBO")
        duration = match["durationSeconds"]

        for p in match["players"]:
            if p["steamAccountId"] == steam_id:
                result = {
                    "match_id": match_id,
                    "kills": p["kills"],
                    "deaths": p["deaths"],
                    "assists": p["assists"],
                    "gpm": p["goldPerMinute"],
                    "xpm": p["experiencePerMinute"],
                    "last_hits": p["numLastHits"],
                    "hero_name": p["hero"]["name"],
                    "won": p["isVictory"],
                    "duration": duration,
                    "is_turbo": is_turbo
                }

                print(f"\n🎯 Match {match_id} — {p['hero']['name']}")
                for k, v in result.items():
                    print(f"  {k}: {v}")
                print("")  # newline for clarity

                return result

        print("❌ Could not find player in match.")
        return None

    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        print("Raw response:", res.text)
        return None
