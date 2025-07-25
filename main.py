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

def get_latest_match(steam_id32):
    url = f"https://api.opendota.com/api/players/{steam_id32}/recentMatches"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Error fetching match for {steam_id32}: {res.text}")
        return None

    data = res.json()
    if not data:
        return None
    return data[0]

def format_message(name, match):
    kda = f"{match['kills']}/{match['deaths']}/{match['assists']}"
    result = "Win" if match['radiant_win'] == (match['player_slot'] < 128) else "Loss"
    duration = time.strftime("%Mm%Ss", time.gmtime(match['duration']))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"
    
    return f"🕹️ **{name}** just played match `{match['match_id']}` – `{kda}` – **{result}** – {duration}\n{match_url}"

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
    if match['match_id'] != last_id:
        message = format_message(name, match)
        post_to_discord(message)
        state[str(steam_id)] = match['match_id']

# Save updated state
with open("state.json", "w") as f:
    json.dump(state, f, indent=2)
