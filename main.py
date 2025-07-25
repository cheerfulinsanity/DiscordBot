import requests
import json
import time

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Load or initialize state
try:
    with open("state.json", "r") as f:
        state = json.load(f)
except FileNotFoundError:
    state = {}

GRAPHQL_URL = "https://api.stratz.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {config['stratz_api_key']}",
    "Content-Type": "application/json"
}

def get_latest_match(steam_id32):
    query = {
        "query": """
        query ($steamId: Int!) {
            player(steamAccountId: $steamId) {
                matches(request: { take: 1 }) {
                    id
                    didWin
                    durationSeconds
                    hero {
                        displayName
                    }
                    stats {
                        kills
                        deaths
                        assists
                    }
                }
            }
        }
        """,
        "variables": {
            "steamId": steam_id32
        }
    }

    res = requests.post(GRAPHQL_URL, headers=HEADERS, json=query)
    if res.status_code != 200:
        print(f"Error fetching match for {steam_id32}: {res.text}")
        return None

    data = res.json()
    matches = data.get("data", {}).get("player", {}).get("matches", [])
    if not matches:
        return None
    return matches[0]

def format_message(name, match):
    duration = time.strftime("%Mm%Ss", time.gmtime(match['durationSeconds']))
    result = "Win" if match['didWin'] else "Loss"
    kda = f"{match['stats']['kills']}/{match['stats']['deaths']}/{match['stats']['assists']}"
    hero = match['hero']['displayName']
    match_url = f"https://stratz.com/match/{match['id']}"

    return f"🕹️ **{name}** just played **{hero}** – `{kda}` – **{result}** – {duration}\n{match_url}"

def post_to_discord(message):
    payload = {"content": message}
    r = requests.post(config['webhook_url'], json=payload)
    if r.status_code != 204 and r.status_code != 200:
        print(f"Failed to send message: {r.text}")

# MAIN LOOP
for name, steam_id in config['players'].items():
    match = get_latest_match(steam_id)
    if not match:
        continue

    last_id = state.get(str(steam_id))
    if match['id'] != last_id:
        message = format_message(name, match)
        post_to_discord(message)
        state[str(steam_id)] = match['id']

# Save updated state
with open("state.json", "w") as f:
    json.dump(state, f, indent=2)
