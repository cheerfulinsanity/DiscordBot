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

# ENV from GitHub Secrets or Railway
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
        if response.status_code == 200:
            for hero in response.json():
                HERO_ID_TO_NAME[hero["id"]] = hero["localized_name"]
        else:
            print("⚠️ Failed to fetch hero names:", response.text)
    except Exception as e:
        print("⚠️ Exception fetching hero names:", str(e))

def load_state():
    r = requests.get(GIST_API_URL, headers=GIST_HEADERS)
    if r.status_code == 200:
        return json.loads(r.json()["files"]["state.json"]["content"])
    else:
        print("⚠️ Could not load state.json from Gist")
        return {}

def save_state(state):
    payload = {
        "files": {
            "state.json": {
                "content": json.dumps(state, indent=2)
            }
        }
    }
    r = requests.patch(GIST_API_URL, headers=GIST_HEADERS, json=payload)
    if r.status_code != 200:
        print("⚠️ Failed to update Gist state:", r.text)

def get_latest_full_match(steam_id32):
    url = f"https://api.opendota.com/api/players/{steam_id32}/recentMatches"
    r = requests.get(url)
    if r.status_code != 200:
        print(f"⚠️ Error fetching matches for {steam_id32}")
        return None

    matches = r.json()
    if not matches:
        return None

    for match in matches:
        match_id = match["match_id"]
        detail = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
        if detail.status_code != 200:
            continue

        match_data = detail.json()
        player_data = next((p for p in match_data["players"] if p["account_id"] == steam_id32), None)

        if not player_data:
            print(f"⚠️ Player {steam_id32} not found in match {match_id}")
            continue

        if player_data.get("leaver_status", 0) != 0:
            print(f"⚠️ Player left early — leaver_status = {player_data['leaver_status']}")
            continue

        player_slot = player_data["player_slot"]
        is_radiant = player_slot < 128
        radiant_win = match_data.get("radiant_win")
        won = (radiant_win and is_radiant) or (not radiant_win and not is_radiant)

        hero_id = player_data["hero_id"]
        hero_name = HERO_ID_TO_NAME.get(hero_id, "Unknown Hero")
        is_turbo = match_data.get("game_mode") == 23

        # Extract stats for player's team
        team_stats = []
        for p in match_data["players"]:
            if (p["player_slot"] < 128) == is_radiant:
                team_stats.append({
                    "account_id": p.get("account_id", 0),
                    "kills": p.get("kills", 0),
                    "deaths": p.get("deaths", 0),
                    "assists": p.get("assists", 0),
                    "gpm": p.get("gold_per_min", 0),
                    "xpm": p.get("xp_per_min", 0)
                })

        return {
            "match_id": match_id,
            "account_id": steam_id32,
            "kills": player_data["kills"],
            "deaths": player_data["deaths"],
            "assists": player_data["assists"],
            "last_hits": player_data["last_hits"],
            "denies": player_data["denies"],
            "gpm": player_data["gold_per_min"],
            "xpm": player_data["xp_per_min"],
            "player_slot": player_slot,
            "radiant_win": radiant_win,
            "duration": match_data["duration"],
            "hero_name": hero_name,
            "won": won,
            "is_turbo": is_turbo,
            "invalid": False,
            "team_stats": team_stats
        }

def post_to_discord(message):
    if config.get("test_mode", False):
        print("TEST MODE ENABLED — would have posted:\n", message)
        return
    payload = {"content": message}
    r = requests.post(config['webhook_url'], json=payload)
    if r.status_code not in [200, 204]:
        print("⚠️ Failed to send message to Discord:", r.text)

def format_message(name, match):
    k, d, a = match['kills'], match['deaths'], match['assists']
    duration = time.strftime("%Mm%Ss", time.gmtime(match['duration']))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"
    is_turbo = match.get("is_turbo", False)

    match_type_label = f"{'Victory!' if match['won'] else 'Defeat.'}"
    if is_turbo:
        match_type_label += " (Turbo Match)"

    hero_name = match['hero_name']
    baseline = HERO_BASELINE_MAP.get(hero_name)
    roles = HERO_ROLES.get(hero_name, [])

    tag_line = "did something."
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

        feedback = generate_feedback(
            player_stats,
            baseline,
            roles,
            is_turbo=is_turbo,
            team_stats=match.get("team_stats"),
            steam_id=match.get("account_id")
        )

        tier = feedback.get("tier", "").lower()
        tier_tag = {
            "excellent": "smashed",
            "solid": "did_work",
            "neutral": "even_game",
            "underperformed": "fed"
        }.get(tier)

        if tier_tag:
            flavor_block = FEEDBACK_LIBRARY.get(f"tag_{tier_tag}")
            if flavor_block:
                tag_line = random.choice(flavor_block["lines"][0])

    msg = (
        f"{'🟢' if match['won'] else '🔴'} **{name}** went `{k}/{d}/{a}` — {tag_line}\n"
        f"**{match_type_label}** | ⏱ {duration}\n"
        f"🔗 {match_url}"
    )

    if baseline and roles:
        msg += f"\n\n🎯 **Stats vs Avg ({hero_name})**\n"
        for line in feedback.get("lines", []):
            short = line.replace("Your ", "").replace(" was ", ": ").replace(" vs avg ", " vs ")
            msg += f"- {short}\n"
        if "advice" in feedback and feedback["advice"]:
            msg += f"\n🛠️ **Advice**\n" + "\n".join(f"- {tip}" for tip in feedback["advice"])

    if "team_context" in feedback and feedback["team_context"]:
        ctx = feedback["team_context"]
        msg += f"\n\n🛡️ **Team Role**: {ctx['tag']}\n"
        msg += f"Impact Rank: {ctx['impact_rank']} | GPM Rank: {ctx['gpm_rank']} | XPM Rank: {ctx['xpm_rank']}\n"
        msg += f"💬 *{ctx['summary_line']}*"

    return msg.strip()

# === Callable main logic ===
def run_bot():
    load_hero_names()
    state = load_state()
    for name, steam_id in config["players"].items():
        match = get_latest_full_match(steam_id)
        if not match or match.get("invalid"):
            continue
        match_id = match["match_id"]
        if str(steam_id) in state and state[str(steam_id)] == match_id:
            continue
        msg = format_message(name, match)
        post_to_discord(msg)
        state[str(steam_id)] = match_id
    save_state(state)

if __name__ == "__main__":
    run_bot()
