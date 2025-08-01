# bot/stratz.py

import requests
import json
import os
from bot.throttle import throttle  # ✅ Throttle enforcement here

STRATZ_URL = "https://api.stratz.com/graphql"

HEADERS_TEMPLATE = {
    "User-Agent": "STRATZ_API",
    "Content-Type": "application/json"
}


def post_stratz_query(query: str, variables: dict, token: str, timeout: int = 10) -> dict | None:
    """
    Shared Stratz POST helper: applies headers, rate limits, and handles errors.
    """
    throttle()
    headers = HEADERS_TEMPLATE | {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            STRATZ_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=timeout
        )

        if response.status_code != 200:
            print(f"❌ Stratz returned HTTP {response.status_code}: {response.text}")
            return None

        try:
            parsed_data = response.json()
        except Exception as e:
            print(f"❌ Failed to parse JSON response: {e}")
            return None

        if "errors" in parsed_data:
            print(f"❌ Stratz GraphQL error:\n{json.dumps(parsed_data['errors'], indent=2)}")
            return None

        return parsed_data.get("data")

    except Exception as e:
        print(f"❌ Error posting to Stratz: {e}")
        return None


def fetch_latest_match(steam_id: int, token: str) -> dict | None:
    """
    Fetch most recent match (any mode) for the given Steam32 ID.
    """
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: {take: 1}) {
          id
          gameMode
          players {
            steamAccountId
            hero { name }
            isVictory
            kills
            deaths
            assists
          }
        }
      }
    }
    """
    variables = {"steamId": steam_id}
    data = post_stratz_query(query, variables, token)

    if not data:
        return None

    player_data = data.get("player")
    if not player_data:
        print(f"⚠️ No player data returned for Steam ID {steam_id}")
        return None

    matches = player_data.get("matches", [])
    if not matches:
        print(f"⚠️ No recent matches found for {steam_id}")
        return None

    match = matches[0]
    players = match.get("players", [])
    player = next((p for p in players if p.get("steamAccountId") == steam_id), None)
    if not player:
        print(f"⚠️ Tracked player not found in match {match['id']}")
        return None

    return {
        "match_id": match["id"],
        "game_mode": match.get("gameMode", 0),
        "hero_name": player["hero"]["name"],  # leave cleanup to formatter
        "kills": player["kills"],
        "deaths": player["deaths"],
        "assists": player["assists"],
        "won": player["isVictory"],
    }


def fetch_full_match(steam_id: int, match_id: int, token: str) -> dict | None:
    """
    Full match data query with extended player + stat info.
    """
    query = """
    query ($matchId: Long!) {
      match(id: $matchId) {
        id
        gameMode
        durationSeconds
        startDateTime
        players {
          steamAccountId
          isVictory
          isRadiant
          lane
          role
          position
          partyId
          kills
          deaths
          assists
          goldPerMinute
          experiencePerMinute
          numLastHits
          imp
          item0Id
          item1Id
          item2Id
          item3Id
          item4Id
          item5Id
          neutral0Id
          backpack0Id
          backpack1Id
          backpack2Id
          isRandom
          intentionalFeeding
          hero {
            id
            name
            displayName
          }
          stats {
            level
            campStack
            itemPurchases { itemId time }
            killEvents { time target }
            deathEvents { time }
            assistEvents { time target }
            wardDestruction {
              time
            }
          }
        }
      }
    }
    """
    variables = {"matchId": match_id}
    data = post_stratz_query(query, variables, token, timeout=15)

    if not data:
        return None

    if os.getenv("DEBUG_MODE") == "1":
        print("🔎 Full match response:")
        print(json.dumps(data, indent=2))

    return data.get("match")
