import json
import os
import requests

# --- Shared Stratz query runner ---
def post_stratz_query(query: str, variables: dict, token: str, timeout: int = 10) -> dict | None:
    headers = {
        "User-Agent": "STRATZ_API",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.stratz.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=timeout
        )
        response.raise_for_status()
        return response.json().get("data")
    except Exception as e:
        print(f"❌ Stratz query failed: {e}")
        return None

# --- Minimal match summary: for checking most recent match ID ---
def fetch_latest_match(steam_id: int, token: str) -> int | None:
    """
    Fetch the most recent match ID for a given Steam32 ID.
    Used for polling latest match played.
    """
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: { take: 1 }) {
          id
        }
      }
    }
    """
    variables = {"steamId": steam_id}
    data = post_stratz_query(query, variables, token)

    if not data or "player" not in data or not data["player"].get("matches"):
        return None

    return data["player"]["matches"][0]["id"]

# --- Full match payload including extended stats and timeline ---
def fetch_full_match(steam_id: int, match_id: int, token: str) -> dict | None:
    """
    Full match data query with extended player + stat info (v4-ready).
    """
    query = """
    query ($matchId: Long!) {
      match(id: $matchId) {
        id
        durationSeconds
        gameMode
        startDateTime
        players {
          steamAccountId
          isVictory
          isRadiant
          lane
          role
          roleBasic
          position
          partyId
          behavior
          intentionalFeeding
          kills
          deaths
          assists
          imp
          gold
          goldSpent
          networth
          goldPerMinute
          experiencePerMinute
          level
          item0Id
          item1Id
          item2Id
          item3Id
          item4Id
          item5Id
          backpack0Id
          backpack1Id
          backpack2Id
          neutral0Id
          hero {
            id
            name
            displayName
          }
          stats {
            campStack
            networthPerMinute
            experiencePerMinute
            actionsPerMinute
            heroDamagePerMinute
            towerDamagePerMinute
            killEvents { time target }
            deathEvents { time }
            assistEvents { time target }
            wards { time }
            wardDestruction { time }
            courierKills { time }
            runes { time }
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
