import requests
import json
import time
import os
import random

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# ENV from GitHub Secrets
GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"
GIST_HEADERS = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

TAG_MESSAGES = {
    "Smashed": [
        "smashed it.", "had damage numbers you screenshot.",
        "ran the game like a smurf.", "deleted cores for fun.",
        "queued to grief the enemy.", "should probably calm down.",
        "made space... for the morgue.", "styled on them. Pure ego gameplay."
    ],
    "Did Work": [
        "put in solid work.", "held the line.", "delivered the goods.",
        "showed up and clocked in.", "played like an adult.",
        "brought lunch and packed wards.", "kept it tidy.", "did their 20%. Respect."
    ],
    "Got Carried": [
        "got carried harder than a divine 5 in herald queue.",
        "watched the team win.", "still doesn't know what happened, but it’s a W.",
        "survived long enough to see victory.", "was emotional support.",
        "won by being present. Technically.", "contributed moral encouragement.",
        "rode the MMR elevator straight up."
    ],
    "Fed": [
        "fed like they were getting paid for it.", "kept the enemy carry well-fed.",
        "had more deaths than creeps.", "died for every ward and then some.",
        "looked like a turbo player in ranked.", "became part of the jungle rotation — for the enemy.",
        "was reverse couriering gold all game.", "had a direct portal to the fountain."
    ],
    "Support MVP": [
        "babysat like a professional nanny.", "put wards in every bush in the game.",
        "played the game on hard mode — support.", "kept the cores alive and ungrateful.",
        "set up every kill and took none.", "healed, stunned, died — support life.",
        "had more map awareness than the rest of the team combined.",
        "made the enemy jungle feel like a warzone."
    ],
    "Invisible": [
        "played with their monitor off.", "still loading into the game.",
        "took a vow of non-intervention.", "was on mute — and not just comms.",
        "queued up, got lost, came back post-game.", "farmed clarity potions in base.",
        "took the observer role literally.", "entered spectator mode mid-match."
    ],
    "Even Game": [
        "played an honest match.", "was neither the problem nor the solution.",
        "kept things balanced.", "had a mid-tier performance. Literally.",
        "showed up and clicked buttons.", "participated meaningfully. Kinda.",
        "made plays. Also made mistakes.", "was present and accounted for."
    ],
}

def get_score_tag(k, d, a, won):
    if (k + a >= 30 and d <= 5) or (k >= 20 and d <= 3):
        return "Smashed"
    elif (k + a >= 18 and d <= 8):
        return "Did Work"
    elif won and (k + a <= 5) and d >= 10:
        return "Got Carried"
    elif d >= 12 and (k + a) <= 8:
        return "Fed"
    elif a >= 18 and k < 5 and d <= 6:
        return "Support MVP"
    elif k == 0 and a == 0 and d <= 3:
        return "Invisible"
    else:
        return "Even Game"

def load_state():
    try:
        res = requests.get(GIST_API_URL, headers=GIST_HEADERS)
        if res.status_code != 200:
            print("⚠️ Failed to fetch state.json from Gist.")
            return {}
        content = res.json()["files"]["state.json"]["content"]
        return json.loads(content)
    except Exception as e:
        print("⚠️ Error loading state.json:", e)
        return {}

def save_state(state):
    try:
        payload = {
            "files": {
                "state.json": {
                    "content": json.dumps(state, indent=2)
                }
            }
        }
        res = requests.patch(GIST_API_URL, headers=GIST_HEADERS, json=payload)
        if res.status_code != 200:
            print("⚠️ Failed to update Gist:", res.text)
    except Exception as e:
        print("⚠️ Error saving to Gist:", e)

def get_latest_match(steam_id32):
    url = f"https://api.opendota.com/api/players/{steam_id32}/recentMatches"
    res = requests.get(url)
    if res.status_code != 200:
        print(f"Error fetching match for {steam_id32}: {res.text}")
        return None
    data = res.json()
    return data[0] if data else None

def format_message(name, match):
    k, d, a = match['kills'], match['deaths'], match['assists']
    duration = time.strftime("%Mm%Ss", time.gmtime(match['duration']))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"

    is_radiant = match['player_slot'] < 128
    won = (match['radiant_win'] and is_radiant) or (not match['radiant_win'] and not is_radiant)
    result_emoji = "🟢" if won else "🔴"
    result_text = "Victory!" if won else "Defeat."

    tag = get_score_tag(k, d, a, won)
    tag_line = random.choice(TAG_MESSAGES[tag])

    return (
        f"{result_emoji} **{name}** went `{k}/{d}/{a}` — {tag_line}\n"
        f"**{result_text}** | ⏱ {duration}\n"
        f"🔗 {match_url}"
    )

def post_to_discord(message):
    if config.get("test_mode", False):
        print("TEST MODE ENABLED — would have posted:\n", message)
        return
    payload = {"content": message}
    r = requests.post(config['webhook_url'], json=payload)
    if r.status_code not in [200, 204]:
        print("⚠️ Failed to send message to Discord:", r.text)

# Load persistent state from Gist
state = load_state()

# Main loop
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
