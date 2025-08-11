import requests
import os
from bot.throttle import throttle

DEBUG_MODE = os.getenv("DEBUG_MODE", "0") == "1"

def post_stratz_query(query, variables, token, timeout=10):
    """
    Posts a GraphQL query to Stratz with the given variables and token.
    Returns the data dict on success, "quota_exceeded" string on quota hit,
    or None on other failure.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "GuildBot/3.6"
    }
    throttle()
    try:
        resp = requests.post(
            "https://api.stratz.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=timeout
        )
        if resp.status_code == 429:
            return "quota_exceeded"
        if resp.status_code != 200:
            if "quota" in resp.text.lower():
                return "quota_exceeded"
            print(f"❌ Stratz query failed [{resp.status_code}]: {resp.text}")
            return None
        data = resp.json()
        return data.get("data")
    except Exception as e:
        print(f"❌ Error in post_stratz_query: {e}")
        return None


def fetch_latest_match(steam_id: int, token: str):
    """
    Fetches the latest match ID for a given Steam32 ID.
    """
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(take: 1) {
          id
        }
      }
    }
    """
    variables = {"steamId": steam_id}
    data = post_stratz_query(query, variables, token)
    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}
    if not data or not data.get("player") or not data["player"].get("matches"):
        return None
    match_id = data["player"]["matches"][0]["id"]
    return {"match_id": match_id}


def fetch_full_match(steam_id: int, match_id: int, token: str):
    """
    Fetches full match data for analysis.
    Returns the match dict, or {"error": "quota_exceeded"} on quota limit.
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
          isRadiant
          isVictory
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
          heroDamage
          towerDamage
          heroHealing
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
            level
            networthPerMinute
            goldPerMinute
            experiencePerMinute
            actionsPerMinute
            heroDamagePerMinute
            towerDamagePerMinute
            impPerMinute
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
    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}
    if not data or not data.get("match"):
        return None

    if DEBUG_MODE:
        import json
        print(json.dumps(data, indent=2))

    return data["match"]
