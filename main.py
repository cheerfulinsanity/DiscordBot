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

def get_latest_full_match(steam_id32):
    recent_url = f"https://api.opendota.com/api/players/{steam_id32}/recentMatches"
    res = requests.get(recent_url)
    if res.status_code != 200:
        print(f"Error fetching recent matches for {steam_id32}: {res.text}")
        return None
    data = res.json()
    if not data:
        return None
    match_id = data[0]["match_id"]

    match_url = f"https://api.opendota.com/api/matches/{match_id}"
    res = requests.get(match_url)
    if res.status_code != 200:
        print(f"Error fetching match {match_id}: {res.text}")
        return None
    match_data = res.json()

    player_data = next((p for p in match_data["players"] if p["account_id"] == steam_id32), None)
    if not player_data:
        print(f"Player {steam_id32} not found in match {match_id}")
        return None

    hero_id = player_data["hero_id"]
    hero_name = HERO_ID_TO_NAME.get(hero_id, "Unknown Hero")
    is_radiant = player_data["player_slot"] < 128
    won = (match_data["radiant_win"] and is_radiant) or (not match_data["radiant_win"] and not is_radiant)

    match_summary = {
        "match_id": match_id,
        "kills": player_data["kills"],
        "deaths": player_data["deaths"],
        "assists": player_data["assists"],
        "last_hits": player_data["last_hits"],
        "denies": player_data["denies"],
        "gpm": player_data["gold_per_min"],
        "xpm": player_data["xp_per_min"],
        "player_slot": player_data["player_slot"],
        "radiant_win": match_data["radiant_win"],
        "duration": match_data["duration"],
        "game_mode": match_data["game_mode"],
        "hero_name": hero_name,
        "won": won
    }

    return match_summary

def format_message(name, match, is_turbo, is_group=False):
    k, d, a = match['kills'], match['deaths'], match['assists']
    duration = time.strftime("%Mm%Ss", time.gmtime(match['duration']))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"

    tag = get_score_tag(k, d, a, match["won"])
    flavor_block = FEEDBACK_LIBRARY.get(f"tag_{tag.lower()}")
    tag_line = random.choice(flavor_block["lines"][0]) if flavor_block else "did something."

    header = f"{'🟢' if match['won'] else '🔴'} 📌 **{name}** went `{k}/{d}/{a}` — {tag_line}" if is_group else f"{'🟢' if match['won'] else '🔴'} **{name}** went `{k}/{d}/{a}` — {tag_line}"
    result_line = f"**{'Guild Squad' if is_group else 'Guild Member'} {'Victory!' if match['won'] else 'Defeat.'} ({'Turbo ' if is_turbo else ''}Match {match['match_id']})**"
    
    msg = f"{header}\n{result_line} | ⏱ {duration}\n🔗 {match_url}"

    hero_name = match['hero_name']
    baseline = HERO_BASELINE_MAP.get(hero_name)
    roles = HERO_ROLES.get(hero_name, [])
    if baseline and roles:
        player_stats = {
            "kills": k,
            "deaths": d,
            "assists": a,
            "last_hits": match.get("last_hits", 0),
            "denies": match.get("denies", 0),
            "gpm": match.get("gpm", 0),
            "xpm": match.get("xpm", 0)
        }
        feedback = generate_feedback(player_stats, baseline, roles)
        msg += f"\n\n🎯 **Stats vs Avg ({hero_name})**\n"
        for line in feedback.get("lines", []):
            if is_turbo and ("GPM" in line or "XPM" in line):
                continue
            short = line.replace("Your ", "").replace(" was ", ": ").replace(" vs avg ", " vs ")
            msg += f"- {short}\n"
        if "advice" in feedback and feedback["advice"]:
            msg += f"\n🛠️ **Advice**\n" + "\n".join(f"- {tip}" for tip in feedback["advice"])
    return msg.strip()

def post_to_discord(message):
    if config.get("test_mode", False):
        print("TEST MODE ENABLED — would have posted:\n", message)
        return
    payload = {"content": message}
    r = requests.post(config['webhook_url'], json=payload)
    if r.status_code not in [200, 204]:
        print("⚠️ Failed to send message to Discord:", r.text)

# Main loop
state = load_state()
match_groups = {}

for name, steam_id in config["players"].items():
    match = get_latest_full_match(steam_id)
    if not match:
        continue
    match_id = str(match["match_id"])
    if str(steam_id) in state and state[str(steam_id)] == match_id:
        continue
    if match_id not in match_groups:
        match_groups[match_id] = []
    match_groups[match_id].append((name, steam_id, match))

for match_id, players in match_groups.items():
    is_turbo = players[0][2]["game_mode"] == 23
    is_group = len(players) > 1
    messages = []
    for name, _, match in players:
        msg = format_message(name, match, is_turbo, is_group)
        messages.append(msg)
        state[str(match["player_slot"])] = match["match_id"]
    full_message = "\n\n".join(messages)
    post_to_discord(full_message)

save_state(state)
