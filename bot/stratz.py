# bot/stratz.py

import requests

def fetch_latest_match(steam_id: int, token: str) -> dict:
    query = """
    query GetLatestMatch($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: { take: 1 }) {
          id
          durationSeconds
          players {
            steamAccountId
            isVictory
            hero {
              id
              name
            }
            kills
            deaths
            assists
          }
        }
      }
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "STRATZ_API"
    }

    payload = {
        "query": query,
        "variables": { "steamId": steam_id }
    }

    res = requests.post("https://api.stratz.com/graphql", headers=headers, json=payload)
    res.raise_for_status()
    data = res.json()

    matches = data["data"]["player"]["matches"]
    if not matches:
        raise ValueError("No matches found")

    match = matches[0]

    for p in match["players"]:
        if p["steamAccountId"] == steam_id:
            return {
                "match_id": match["id"],
                "hero_name": p["hero"]["name"],
                "kills": p["kills"],
                "deaths": p["deaths"],
                "assists": p["assists"],
                "won": p["isVictory"]
            }

    raise ValueError("Player not found in match")
