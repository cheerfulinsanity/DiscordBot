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

# Build hero_id → localized_name map
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

def get_latest_match_id(steam_id):
    try:
        url = f"https://api.opendota.com/api/players/{steam_id}/recentMatches"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        matches = r.json()
        if not matches:
            return None
        return matches[0].get("match_id")
    except Exception as e:
        print(f"⚠️ Failed to get recent match for {steam_id}: {e}")
        return None

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

    # First pass: identify new matches
    pending = []
    for name, steam_id in config["players"].items():
        latest_id = get_latest_match_id(steam_id)
        if not latest_id:
            print(f"⏭️ Skipping {name} — no recent match")
            continue
        if str(steam_id) in state and state[str(steam_id)] == str(latest_id):
            print(f"✅ {name} already posted match {latest_id}")
            continue
        print(f"📥 Queued for fetch: {name} ({latest_id})")
        pending.append((name, steam_id, latest_id))

    print(f"📋 {len(pending)} players have new matches")

    # Second pass: fetch and post full matches
    for i, (name, steam_id, match_id) in enumerate(pending):
        try:
            match = get_latest_full_match(steam_id, hero_id_to_name)
            if not is_valid_match(match):
                print(f"⏭️ Skipping {name} — match invalid or too short")
                continue

            msg = format_message(name, match, HERO_ROLES, HERO_BASELINE_MAP)
            if post_to_discord(msg):
                state[str(steam_id)] = str(match_id)
                print(f"✅ Posted match {match_id} for {name}")
            else:
                print(f"⚠️ Failed to post for {name}, not updating state.")
        except Exception as e:
            print(f"❌ Error processing {name} ({steam_id}): {e}")

        if (i + 1) % 10 == 0:
            time.sleep(2)

    save_state(state)
