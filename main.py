import os
import json
import time
import random
import requests

from feedback_engine import generate_feedback
from feedback_catalog import FEEDBACK_LIBRARY

# === Load Static Data ===
with open("config.json", "r") as f:
    CONFIG = json.load(f)

with open("hero_roles.json", "r") as f:
    HERO_ROLES = json.load(f)

with open("hero_baselines.json", "r") as f:
    HERO_BASELINES = json.load(f)

BASELINE_MAP = {entry["hero"]: entry for entry in HERO_BASELINES}
GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

HERO_ID_TO_NAME = {}
GIST_HEADERS = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"


# === Utilities ===
def load_hero_names():
    try:
        r = requests.get("https://api.opendota.com/api/heroStats")
        r.raise_for_status()
        for h in r.json():
            HERO_ID_TO_NAME[h["id"]] = h["localized_name"]
        print(f"✅ Hero names loaded: {len(HERO_ID_TO_NAME)}")
    except Exception as e:
        print("⚠️ Failed to load hero names:", str(e))


def load_state():
    try:
        r = requests.get(GIST_API_URL, headers=GIST_HEADERS)
        return json.loads(r.json()["files"]["state.json"]["content"])
    except Exception as e:
        print("⚠️ Could not load state.json:", str(e))
        return {}


def save_state(state):
    payload = {
        "files": {
            "state.json": {
                "content": json.dumps(state, indent=2)
            }
        }
    }
    try:
        r = requests.patch(GIST_API_URL, headers=GIST_HEADERS, json=payload)
        if r.status_code != 200:
            print("⚠️ Failed to update Gist:", r.text)
    except Exception as e:
        print("❌ Error saving state:", str(e))


def fetch_match(steam_id):
    try:
        r = requests.get(f"https://api.opendota.com/api/players/{steam_id}/recentMatches")
        r.raise_for_status()
        for match in r.json():
            match_id = match["match_id"]
            detail = requests.get(f"https://api.opendota.com/api/matches/{match_id}")
            if detail.status_code != 200:
                continue
            data = detail.json()
            for p in data["players"]:
                if p.get("account_id") == steam_id:
                    if p.get("leaver_status", 0) != 0:
                        return None
                    hero_name = HERO_ID_TO_NAME.get(p["hero_id"], "Unknown Hero")
                    if hero_name == "Unknown Hero":
                        print(f"⚠️ Unknown hero ID: {p['hero_id']}")
                    is_radiant = p["player_slot"] < 128
                    won = data["radiant_win"] == is_radiant
                    return {
                        "match_id": match_id,
                        "account_id": steam_id,
                        "hero_name": hero_name,
                        "kills": p["kills"],
                        "deaths": p["deaths"],
                        "assists": p["assists"],
                        "last_hits": p["last_hits"],
                        "denies": p["denies"],
                        "gpm": p["gold_per_min"],
                        "xpm": p["xp_per_min"],
                        "duration": data["duration"],
                        "won": won,
                        "is_turbo": data.get("game_mode") == 23,
                        "team_stats": [
                            {
                                "account_id": q.get("account_id", 0),
                                "kills": q.get("kills", 0),
                                "deaths": q.get("deaths", 0),
                                "assists": q.get("assists", 0),
                                "gpm": q.get("gold_per_min", 0),
                                "xpm": q.get("xp_per_min", 0),
                            }
                            for q in data["players"] if (q["player_slot"] < 128) == is_radiant
                        ]
                    }
    except Exception as e:
        print(f"❌ Failed to fetch match for {steam_id}:", str(e))
    return None


def build_message(name, match):
    k, d, a = match["kills"], match["deaths"], match["assists"]
    hero = match["hero_name"]
    baseline = BASELINE_MAP.get(hero)
    roles = HERO_ROLES.get(hero, [])
    turbo = match["is_turbo"]
    duration = time.strftime("%Mm%Ss", time.gmtime(match["duration"]))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"
    result = "Victory!" if match["won"] else "Defeat."

    msg = f"{'🟢' if match['won'] else '🔴'} **{name}** went `{k}/{d}/{a}` — "
    feedback = None

    if baseline and roles:
        feedback = generate_feedback(
            player_stats=match,
            hero_baseline=baseline,
            roles=roles,
            is_turbo=turbo,
            team_stats=match["team_stats"],
            steam_id=match["account_id"]
        )

    if feedback:
        ctx = feedback.get("team_context")
        if ctx:
            msg += f"🛡️ Team Role: {ctx['tag']} | GPM Rank: {ctx['gpm_rank']} | Impact Rank: {ctx['impact_rank']}"
        else:
            msg += random.choice(FEEDBACK_LIBRARY.get("tag_neutral", {}).get("lines", [[""]])[0])
        msg += f"\n**{result}** | ⏱ {duration}\n🔗 {match_url}"

        msg += f"\n\n🎯 **Stats vs Avg ({hero})**"
        for line in feedback["lines"]:
            msg += f"\n- {line}"
        if feedback.get("advice"):
            msg += "\n\n🛠️ **Advice**"
            for tip in feedback["advice"]:
                msg += f"\n- {tip}"
        if ctx:
            msg += f"\n\n💬 *{ctx['summary_line']}*"
    else:
        msg += f"{result} | ⏱ {duration}\n🔗 {match_url}"

    return msg.strip()


def post_to_discord(msg):
    if CONFIG.get("test_mode", False):
        print("TEST MODE — Message:\n", msg)
        return True
    r = requests.post(CONFIG["webhook_url"], json={"content": msg})
    if r.status_code in [200, 204]:
        return True
    print("⚠️ Failed to post to Discord:", r.text)
    return False


# === Entrypoint ===
def run_bot():
    print("▶️ Starting bot...")
    load_hero_names()
    state = load_state()

    for name, steam_id in CONFIG["players"].items():
        try:
            match = fetch_match(steam_id)
            if not match:
                print(f"Skipping {name} — no valid match")
                continue
            if str(steam_id) in state and state[str(steam_id)] == match["match_id"]:
                print(f"{name} already posted match {match['match_id']}")
                continue
            msg = build_message(name, match)
            if post_to_discord(msg):
                state[str(steam_id)] = match["match_id"]
                print(f"✅ Posted for {name}: {match['match_id']}")
            else:
                print(f"⚠️ Not saving match due to failed post for {name}")
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")

    save_state(state)


if __name__ == "__main__":
    run_bot()
