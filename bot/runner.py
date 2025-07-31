# bot/runner.py

import os
from time import sleep
from bot.fetch import get_latest_new_match, get_full_match_data
from bot.formatter import format_match
from bot.gist_state import load_state, save_state
from bot.config import CONFIG
import json
import logging

logging.basicConfig(level=logging.INFO)

def run_bot():
    print("🚀 GuildBot started")

    players = CONFIG["players"]
    print(f"👥 Loaded {len(players)} players from config.json")

    known_match_ids = load_state()
    print("📥 Loaded state.json from GitHub Gist")
    print(f"🔎 Initial state keys: {list(known_match_ids.keys())}")

    token = os.getenv("TOKEN")
    if not token:
        print("❌ No Stratz API token found in environment. Set TOKEN before running.")
        return

    for index, (player_name, player_id) in enumerate(players.items(), start=1):
        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({player_id})...")

        try:
            new_match = get_latest_new_match(player_id, known_match_ids.get(str(player_id)), token)
        except Exception as e:
            print(f"❌ Error checking latest match for {player_name}: {e}")
            continue

        if not new_match:
            print("⏩ No new match. Skipping.")
            continue

        match_id = new_match["match_id"]
        print(f"🆕 New match found: {match_id}")

        full_data = get_full_match_data(player_id, match_id, token)
        if not full_data:
            print(f"❌ Failed to fetch full match data for {player_name}")
            continue

        try:
            hero_name = new_match["hero_name"]
            kills = new_match["kills"]
            deaths = new_match["deaths"]
            assists = new_match["assists"]
            won = new_match["won"]

            print(f"🧙 {player_name} — {hero_name}: {kills}/{deaths}/{assists} — {'🏆 Win' if won else '💀 Loss'} (Match ID: {match_id})")
            print("📊 Performance Analysis:")

            feedback = format_match(
                player_name,
                player_id,
                hero_name,
                kills,
                deaths,
                assists,
                won,
                full_data
            )
            print(feedback)

        except Exception as e:
            print(f"❌ Failed to format match for {player_name}: {e}")
            continue

        known_match_ids[str(player_id)] = match_id
        sleep(1.2)

    # 🧪 Inject a fake match entry to confirm saving works
    known_match_ids["999999999"] = 1234567890

    print(f"📤 Saving updated match IDs:\n{json.dumps(known_match_ids, indent=2)}")
    save_state(known_match_ids)

    print("✅ GuildBot run complete.")
