# bot/stratz.py

import requests
import json
import os  # For DEBUG_MODE

STRATZ_URL = "https://api.stratz.com/graphql"

HEADERS_TEMPLATE = {
    "User-Agent": "STRATZ_API",
    "Content-Type": "application/json"
}


def fetch_latest_match(steam_id: int, token: str) -> dict | None:
    """
    Minimal query to fetch most recent match ID for the given Steam32 ID.
    """
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: {take: 1, gameModeIds: [23]}) {
          id
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
    headers = HEADERS_TEMPLATE | {"Authorization": f"Bearer {token}"}

    try:
        res = requests.post(
            STRATZ_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )

        if res.status_code != 200:
            print(f"❌ Stratz returned HTTP {res.status_code}: {res.text}")
            return None

        data = res.json()

        if "errors" in data:
            print(f"❌ Stratz GraphQL error:\n{json.dumps(data['errors'], indent=2)}")
            return None

        player_data = data.get("data", {}).get("player")
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
            "hero_name": player["hero"]["name"].replace("npc_dota_hero_", ""),
            "kills": player["kills"],
            "deaths": player["deaths"],
            "assists": player["assists"],
            "won": player["isVictory"],
        }

    except Exception as e:
        print(f"❌ Error in fetch_latest_match: {e}")
        return None


def fetch_full_match(steam_id: int, match_id: int, token: str) -> dict | None:
    """
    Full match data query with extended player + stat info.
    """
    query = """
    query ($matchId: Long!) {
      match(id: $matchId) {
        id
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
    headers = HEADERS_TEMPLATE | {"Authorization": f"Bearer {token}"}

    try:
        res = requests.post(
            STRATZ_URL,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=15
        )

        if res.status_code != 200:
            print(f"❌ Stratz returned HTTP {res.status_code}: {res.text}")
            return None

        data = res.json()

        if "errors" in data:
            print(f"❌ GraphQL errors from Stratz:\n{json.dumps(data['errors'], indent=2)}")
            return None

        if os.getenv("DEBUG_MODE") == "1":
            print("🔎 Full match response:")
            print(json.dumps(data, indent=2))

        return data.get("data", {}).get("match")

    except Exception as e:
        print(f"❌ Error in fetch_full_match: {e}")
        return None
