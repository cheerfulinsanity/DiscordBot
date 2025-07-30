# bot/stratz.py

import os
import requests

STRATZ_TOKEN = os.getenv("TOKEN")  # Uses 'TOKEN' as per Render env config

URL = "https://api.stratz.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {STRATZ_TOKEN}",
    "Content-Type": "application/json"
}

QUERY = """
query GetLastMatch($steamId: Long!) {
  player(steamAccountId: $steamId) {
    matches(request: {take: 1}) {
      id
      durationSeconds
      gameMode
      startDateTime
      players {
        steamAccountId
        isVictory
        hero {
          displayName
        }
        kills
        deaths
        assists
        numLastHits
        numDenies
        goldPerMinute
        experiencePerMinute
      }
    }
  }
}
"""

def fetch_latest_stratz_match(steam_id):
    response = requests.post(URL, headers=HEADERS, json={
        "query": QUERY,
        "variables": {"steamId": steam_id}
    })

    if response.status_code != 200:
        raise Exception(f"Stratz API error: {response.status_code} - {response.text}")

    data = response.json()
    match = data["data"]["player"]["matches"][0]
    players = match["players"]

    # Locate the player
    player = next((p for p in players if p["steamAccountId"] == steam_id), None)
    if not player:
        raise Exception("Player not found in match player list")

    return {
        "match_id": match["id"],
        "duration": match["durationSeconds"],
        "won": player["isVictory"],
        "hero_name": player["hero"]["displayName"],
        "kills": player["kills"],
        "deaths": player["deaths"],
        "assists": player["assists"],
        "last_hits": player["numLastHits"],
        "denies": player["numDenies"],
        "gpm": player["goldPerMinute"],
        "xpm": player["experiencePerMinute"],
        "is_turbo": match["gameMode"] == "TURBO",
        "account_id": player["steamAccountId"],
        "team_stats": players
    }
