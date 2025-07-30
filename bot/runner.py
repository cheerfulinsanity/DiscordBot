import requests
import sys
import os

TOKEN = os.getenv("TOKEN")  # Use your 'TOKEN' env var

def test_stratz_fetch_one_player(steam32_id):
    url = "https://api.stratz.com/graphql"
    query = """
    query ($steamAccountId: Int!) {
      player(steamAccountId: $steamAccountId) {
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
    variables = {"steamAccountId": steam32_id}
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "GuildBot/1.0",
    }
    payload = {
        "query": query,
        "variables": variables,
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        matches = data.get("data", {}).get("player", {}).get("matches", [])
        if not matches:
            print(f"No matches found for player {steam32_id}")
            return
        match = matches[0]
        players = match.get("players", [])
        player_data = next((p for p in players if p.get("steamAccountId") == steam32_id), None)
        if not player_data:
            print(f"Player data not found in match for {steam32_id}")
            return

        output = {
            "match_id": match.get("id"),
            "duration": match.get("durationSeconds"),
            "won": player_data.get("isVictory"),
            "hero_name": player_data.get("hero", {}).get("displayName"),
            "kills": player_data.get("kills"),
            "deaths": player_data.get("deaths"),
            "assists": player_data.get("assists"),
            "last_hits": player_data.get("numLastHits"),
            "denies": player_data.get("numDenies"),
            "gpm": player_data.get("goldPerMinute"),
            "xpm": player_data.get("experiencePerMinute"),
            "is_turbo": match.get("gameMode") == "TURBO",
            "account_id": player_data.get("steamAccountId"),
            "team_stats": players,
        }

        print(f"✅ Fetched and flattened match data for player {steam32_id}:\n{output}")

    except requests.HTTPError as e:
        print(f"❌ HTTP error: {e.response.status_code} - {e.response.text[:300]}")
    except Exception as e:
        print(f"❌ Error during fetch: {e}")

if __name__ == "__main__":
    test_player_id = 1051062040
    print(f"Starting fetch test for player {test_player_id}")
    test_stratz_fetch_one_player(test_player_id)
    print("Fetch test complete. Exiting.")
    sys.exit(0)
