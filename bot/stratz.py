import requests
import os

TOKEN = os.getenv("TOKEN")
STRATZ_URL = "https://api.stratz.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "STRATZ_API"
}

QUERY = """
query GetRecentMatch($steamId: Long!) {
  player(steamAccountId: $steamId) {
    matches(request: {take: 1}) {
      id
      durationSeconds
      startDateTime
      players {
        steamAccountId
        isVictory
        hero { id name }
        kills
        deaths
        assists
      }
    }
  }
}
"""

def fetch_recent_match(steam_id):
    payload = {
        "query": QUERY,
        "variables": { "steamId": steam_id }
    }

    res = requests.post(STRATZ_URL, headers=HEADERS, json=payload)
    res.raise_for_status()
    data = res.json()

    try:
        match = data["data"]["player"]["matches"][0]
        players = match["players"]
        for p in players:
            if p["steamAccountId"] == steam_id:
                return {
                    "match_id": match["id"],
                    "duration": match["durationSeconds"],
                    "hero_id": p["hero"]["id"],
                    "hero_name": p["hero"]["name"],
                    "kills": p["kills"],
                    "deaths": p["deaths"],
                    "assists": p["assists"],
                    "won": p["isVictory"]
                }
    except Exception as e:
        raise RuntimeError(f"Failed to parse Stratz match data: {e}")
