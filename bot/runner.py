import os
import requests

TOKEN = os.getenv("TOKEN")  # your Stratz API token

def run_bot():
    steam_id = 1051062040  # example Steam32 ID for test

    url = "https://api.stratz.com/graphql"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    query = {
        "query": """
        query($steamId: Int!) {
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
        """,
        "variables": {"steamId": steam_id}
    }

    response = requests.post(url, json=query, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data: HTTP {response.status_code}")
        print(response.text)
        return

    data = response.json()
    try:
        match = data["data"]["player"]["matches"][0]
        player_data = next(p for p in match["players"] if p["steamAccountId"] == steam_id)
        flattened = {
            "match_id": match["id"],
            "duration": match["durationSeconds"],
            "won": player_data["isVictory"],
            "hero_name": player_data["hero"]["displayName"],
            "kills": player_data["kills"],
            "deaths": player_data["deaths"],
            "assists": player_data["assists"],
            "last_hits": player_data["numLastHits"],
            "denies": player_data["numDenies"],
            "gpm": player_data["goldPerMinute"],
            "xpm": player_data["experiencePerMinute"],
            "is_turbo": match["gameMode"] == "TURBO",
            "account_id": steam_id,
            "team_stats": match["players"]
        }
        print("Fetched player match data:")
        print(flattened)
    except Exception as e:
        print(f"Error processing data: {e}")
