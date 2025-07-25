import requests
import json
import time
import os

# Get token and Gist ID from environment (set via GitHub Actions)
GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

HEADERS = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

def load_state():
    res = requests.get(GIST_API_URL, headers=HEADERS)
    if res.status_code != 200:
        print("⚠️ Failed to fetch state.json from Gist.")
        return {}

    gist_data = res.json()
    file_content = gist_data["files"]["state.json"]["content"]
    return json.loads(file_content)

def save_state(state):
    new_content = json.dumps(state, indent=2)
    payload = {
        "files": {
            "state.json": {
                "content": new_content
            }
        }
    }
    res = requests.patch(GIST_API_URL, headers=HEADERS, json=payload)
    if res.status_code != 200:
        print("⚠️ Failed to update Gist:", res.text)

def get_latest_match(steam_id32):
    url = f"https://api.opendota.com/api/players/{steam_id32}/recentMatches"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Error fetching match for {steam_id32}: {res.text}")
        return None

    data = res.json()
    return data[0] if data else None

def format_message(name, match):
    kda = f"{match['kills']}/{match['deaths']}/{match['assists']}"
    result = "Win" if match['radiant_win'] == (match['player_slot'] < 128) else "Loss"
    duration = time.strftime("%Mm%Ss", time.gmtime(match['duration']))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"
    return f"🕹️ **{name}** just played match `{match['match_id']}` – `{kda}` – **{result}** – {duration}\n{match_url}"

def post_to_discord(message):
    payload = {"content": message}
    r = requests.post(config['webhook_url'], json=payload)
    if r.status_code not in [200, 204]:
        print("⚠️ Failed to send message to Discord:", r.text)

# Load persistent state from Gist
state = load_state()

# Process each player
for name, steam_id in config['players'].items():
    match = get_latest_match(steam_id)
    if not match:
        continue

    last_id = state.get(str(steam_id))
    if match['match_id'] != last_id:
        message = format_message(name, match)
        post_to_discord(message)
        state[str(steam_id)] = match['match_id']

# Save updated state to Gist
save_state(state)
