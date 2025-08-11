# bot/stratz.py

import json
import os
import requests
from bot.throttle import throttle  # ✅ Enforce rate limit before each request

# --- Shared Stratz query runner ---
def post_stratz_query(query: str, variables: dict, token: str, timeout: int = 10) -> dict | str | None:
    """
    POST a GraphQL query to Stratz and return the 'data' object on success.
    On quota exhaustion: return the string 'quota_exceeded'.
    On other failures: return None (callers handle skip/continue logic).
    """
    # A boring, product-style UA often avoids WAF heuristics better than a custom token-y one.
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GuildBot/3.6; +https://example.com/guildbot)",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    throttle()  # ✅ Rate-limit per second/minute/hour caps

    try:
        response = requests.post(
            "https://api.stratz.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=timeout
        )

        # Explicit quota handling
        if response.status_code == 429:
            print("🛑 Stratz API returned 429 Too Many Requests")
            return "quota_exceeded"

        # Better diagnostics for any non-200 to identify CF / auth / schema issues
        if response.status_code != 200:
            safe_headers = {
                # Tiny subset only; avoid dumping everything
                "status": response.status_code,
                "server": response.headers.get("server"),
                "cf-ray": response.headers.get("cf-ray"),
                "content-type": response.headers.get("Content-Type"),
                "date": response.headers.get("Date"),
            }
            snippet = (response.text or "")[:300].replace("\n", " ").strip()
            print(f"⚠️ Stratz non-200: {safe_headers} | body[:300]={snippet}")
            response.raise_for_status()

        # Parse JSON body
        try:
            payload = response.json()
        except Exception as je:
            # If CF or a proxy returned HTML, this will fire
            print(f"❌ Failed to parse JSON from Stratz: {je}")
            text_snippet = (response.text or "")[:200].replace("\n", " ").strip()
            print(f"📎 Body[:200]={text_snippet}")
            return None

        return (payload or {}).get("data")

    except requests.HTTPError as e:
        # Surface HTTP layer issues (403/401/etc.)
        print(f"❌ Stratz query failed: {e}")
        if "429" in str(e):
            return "quota_exceeded"
        return None
    except Exception as e:
        # Network errors, timeouts, etc.
        print(f"❌ Stratz query failed: {e}")
        if "quota" in str(e).lower():
            return "quota_exceeded"
        return None

# --- Minimal match summary: for checking most recent match ID ---
def fetch_latest_match(steam_id: int, token: str) -> dict | None:
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

    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}

    if not data or "player" not in data or not data["player"].get("matches"):
        return None

    return {"match_id": data["player"]["matches"][0]["id"]}

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

    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}

    if not data:
        return None

    if os.getenv("DEBUG_MODE") == "1":
        print("🔎 Full match response:")
        print(json.dumps(data, indent=2))

    return data.get("match")
