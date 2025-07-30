import requests
import sys

def test_stratz_fetch(steam32_id):
    url = "https://api.stratz.com/graphql"
    query = """
    query ($accountId: Int!) {
      player(accountId: $accountId) {
        steamAccount {
          id
          name
        }
        recentMatches {
          id
          startDateTime
          durationSeconds
          kills
          deaths
          assists
        }
      }
    }
    """
    variables = {"accountId": steam32_id}
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "variables": variables,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.headers.get("Content-Type", "").startswith("application/json"):
            data = response.json()
            print(f"✅ Success fetching data for player {steam32_id}:\n{data}")
        else:
            print(f"❌ Blocked or HTML received for player {steam32_id}:\n{response.text[:300]}")
    except Exception as e:
        print(f"❌ Error fetching data for player {steam32_id}: {e}")

if __name__ == "__main__":
    # Replace this Steam32 ID with your target player for test
    test_player_id = 1051062040

    print(f"Starting minimal fetch for one player: {test_player_id}")
    test_stratz_fetch(test_player_id)
    print("Finished minimal fetch, exiting.")
    sys.exit(0)
