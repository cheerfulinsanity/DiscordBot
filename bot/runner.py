# bot/runner.py

import os
import json
import time
import requests

from bot.opendota import fetch_hero_stats
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

def build_hero_id_map():
    hero_id_to_name = {}
    heroes = fetch_hero_stats()
    for hero in heroes:
        hero_id_to_name[hero["id"]] = hero["localized_name"]
    return hero_id_to_name

def post_to_discord(message):
    if config.get("test_mode", False):
        print("🧪 TEST MODE — would have posted:\n", message)
        return True
    try:
        r = requests.post(config["webhook_url"], json={"content": message})
        print(f"📤 Discord POST status: {r.status_code}")
        if r.status_code in [200, 204]:
            return True
        print("⚠️ Failed to send to Discord:", r.text)
    except Exception as e:
        print("⚠️ Exception during Discord post:", e)
    return False

def is_valid_match(match):
    if not match:
        return False
    if match.get("invalid") or match.get("duration", 0) < 300:
        return False
    if match.get("lobby_type") == 7:  # practice bot
        return False
    if match.get("game_mode") not in {1, 2, 22, 23}:  # AP, CM, Turbo, etc.
        return False
    return True

def run_bot():
    print("🔁 Running GuildBot...")
    hero_id_to_name = build_hero_id_map()
    state = load_state()

    for name, steam_id in config["players"].items():
        try:
            match = get_latest_full_match(steam_id, hero_id_to_name)
            if not is_valid_match(match):
                print(f"⏭️ Skipping {name} — invalid or too short")
                continue

            match_id = str(match["match_id"])
            if state.get(str(steam_id)) == match_id:
                print(f"✅ {name} already posted match {match_id}")
                continue

            print(f"📥 New match for {name}: {match_id}")
            message = format_message(name, match, HERO_ROLES, HERO_BASELINE_MAP)

            if post_to_discord(message):
                state[str(steam_id)] = match_id
                print(f"✅ Posted match for {name}")
            else:
                print(f"⚠️ Failed to post for {name}, skipping state update.")
        except Exception as e:
            print(f"❌ Error processing {name} ({steam_id}): {e}")

    # Dummy entry to confirm save still works
    state["999999999"] = "1234567890"

    save_state(state)
