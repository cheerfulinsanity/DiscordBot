import requests
import json
import time
import os
import random
from feedback_engine import generate_feedback
from feedback_catalog import FEEDBACK_LIBRARY

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Load hero role and baseline data
with open("hero_roles.json", "r") as f:
    HERO_ROLES = json.load(f)

with open("hero_baselines.json", "r") as f:
    HERO_BASELINES = json.load(f)

HERO_BASELINE_MAP = {h["hero"]: h for h in HERO_BASELINES}

# ENV from GitHub Secrets
GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"
GIST_HEADERS = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Load hero ID to name map from OpenDota
HERO_ID_TO_NAME = {}

def load_hero_names():
    global HERO_ID_TO_NAME
    try:
        response = requests.get("https://api.opendota.com/api/heroStats")
        for h in response.json():
            HERO_ID_TO_NAME[h["id"]] = h["localized_name"]
    except Exception as e:
        print("⚠️ Failed to load hero names:", e)

load_hero_names()

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

def get_match_data(match_id):
    url = f"https://api.opendota.com/api/matches/{match_id}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    return res.json()

def get_latest_match_id(steam_id32):
    url = f"https://api.opendota.com/api/players/{steam_id32}/recentMatches"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    return data[0]["match_id"] if data else None

def extract_player_summary(player_data, match_data):
    hero_id = player_data["hero_id"]
    hero_name = HERO_ID_TO_NAME.get(hero_id, "Unknown Hero")
    is_radiant = player_data["player_slot"] < 128
    won = (match_data["radiant_win"] and is_radiant) or (not match_data["radiant_win"] and not is_radiant)
    return {
        "account_id": player_data["account_id"],
        "hero_name": hero_name,
        "kills": player_data["kills"],
        "deaths": player_data["deaths"],
        "assists": player_data["assists"],
        "last_hits": player_data["last_hits"],
        "denies": player_data["denies"],
        "gpm": player_data["gold_per_min"],
        "xpm": player_data["xp_per_min"],
        "player_slot": player_data["player_slot"],
        "won": won
    }

def format_group_message(match_data, guild_players):
    duration = time.strftime("%Mm%Ss", time.gmtime(match_data["duration"]))
    match_url = f"https://www.opendota.com/matches/{match_data['match_id']}"
    result_icon = "🟢" if match_data["radiant_win"] else "🔴"

    msg = f"{result_icon} **Guild Squad {'Victory!' if match_data['radiant_win'] else 'Defeat.'}** (Match {match_data['match_id']}) | ⏱ {duration}\n{match_url}\n"

    for p in guild_players:
        tag = get_score_tag(p['kills'], p['deaths'], p['assists'], p['won'])
        flavor = FEEDBACK_LIBRARY.get(f"tag_{tag.lower()}")
        line = random.choice(flavor["lines"][0]) if flavor else "played a game."
        name = next(k for k, v in config["players"].items() if v == p["account_id"])
        msg += f"\n**{name}** went `{p['kills']}/{p['deaths']}/{p['assists']}` — {line}"

    msg += "\n\n🎯 **Stats vs Avg**"
    for p in guild_players:
        baseline = HERO_BASELINE_MAP.get(p['hero_name'])
        roles = HERO_ROLES.get(p['hero_name'], [])
        if not baseline:
            continue
        stats = {k: p[k] for k in ["kills", "deaths", "assists", "last_hits", "denies", "gpm", "xpm"]}
        feedback = generate_feedback(stats, baseline, roles)
        name = next(k for k, v in config["players"].items() if v == p["account_id"])
        msg += f"\n{name} ({p['hero_name']})"
        for line in feedback.get("lines", []):
            short = line.replace("Your ", "").replace(" was ", ": ").replace(" vs avg ", " vs ")
            msg += f"\n- {short}"
        if feedback.get("advice"):
            msg += f"\n🛠️ Advice"
            for tip in feedback["advice"]:
                msg += f"\n- {tip}"

    return msg.strip()

def post_to_discord(message):
    if config.get("test_mode", False):
        print("TEST MODE ENABLED — would have posted:\n", message)
        return
    r = requests.post(config['webhook_url'], json={"content": message})
    if r.status_code not in [200, 204]:
        print("⚠️ Failed to send message to Discord:", r.text)

# Main Logic
state = load_state()
latest_matches = {}

for name, steam_id in config["players"].items():
    match_id = get_latest_match_id(steam_id)
    if not match_id:
        continue
    if str(steam_id) in state and state[str(steam_id)] == match_id:
        continue
    latest_matches.setdefault(match_id, []).append(steam_id)

for match_id, player_ids in latest_matches.items():
    if len(player_ids) < 1:
        continue
    match_data = get_match_data(match_id)
    if not match_data:
        continue

    guild_players = []
    for p in match_data["players"]:
        if p["account_id"] in player_ids:
            guild_players.append(extract_player_summary(p, match_data))

    if not guild_players:
        continue

    message = format_group_message(match_data, guild_players)
    post_to_discord(message)

    for p in guild_players:
        state[str(p["account_id"])] = match_id

save_state(state)
