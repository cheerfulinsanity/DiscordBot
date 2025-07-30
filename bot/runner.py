# bot/runner.py

import os
import json
import time
import requests

from bot.fetch import get_latest_full_match
from bot.formatter import format_message
from bot.gist_state import load_state, save_state

# Load static data
with open("data/config.json") as f:
    config = json.load(f)

with open("data/hero_roles.json") as f:
    HERO_ROLES = json.load(f)

with open("data/hero_baselines.json") as f:
    raw_baselines = json.load(f)
    HERO_BASELINE_MAP = {entry["hero"]: entry for entry in raw_baselines}

def post_to_discord(message):
    if config.get("test_mode", False):
        print("TEST MODE — would have posted:\n", message)
        return True
    try:
        r = requests.post(config["webhook_url"], json={"content": message})
        if r.status_code in [200, 204]:
            return True
        print("⚠️ Failed to send to Discord:", r.text)
    except Exception as e:
        print("⚠️ Exception during Discord post:", e)
    return False

def run_bot():
    print("🔁 Running GuildBot...")
    state = load_state()

    for name, steam_id in config["players"].items():
        try:
            match = get_latest_full_match(steam_id)
            if not match or match.get("invalid"):
                print(f"⏭️ Skipping {name} — no valid match")
                continue

            match_id = str(match["match_id"])
            if str(steam_id) in state and state[str(steam_id)] == match_id:
                print(f"✅ {name} already posted match {match_id}")
                continue

            msg = format_message(name, match, HERO_ROLES, HERO_BASELINE_MAP)
            if post_to_discord(msg):
                state[str(steam_id)] = match_id
            else:
                print(f"⚠️ Failed to post for {name}, not updating state.")
        except Exception as e:
            print(f"❌ Error processing {name} ({steam_id}): {e}")

        time.sleep(1.0)  # avoid Discord and Stratz rate limits

    save_state(state)
