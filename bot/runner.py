# bot/runner.py

import os
import json
import time
from bot.stratz import fetch_latest_match

CONFIG_PATH = "data/config.json"
TOKEN = os.getenv("TOKEN")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_bot():
    print("🚀 GuildBot started")

    try:
        if not TOKEN:
            print("❌ TOKEN is missing!")
            return

        config = load_config()
        players = config.get("players", {})

        for i, (name, steam_id) in enumerate(players.items(), 1):
            print(f"🔍 [{i}/{len(players)}] Fetching match for {name} ({steam_id})...")
            try:
                match = fetch_latest_match(steam_id, TOKEN)
                print(
                    f"🧙 {name} — {match['hero_name']}: {match['kills']}/"
                    f"{match['deaths']}/{match['assists']} — "
                    f"{'🏆 Win' if match['won'] else '💀 Loss'} "
                    f"(Match ID: {match['match_id']})"
                )
            except Exception as e:
                print(f"❌ Failed to fetch {name} ({steam_id}): {e}")

            time.sleep(0.25)

        print("✅ GuildBot run complete.")
    except Exception as outer:
        print(f"❌ CRASH in run_bot(): {outer}")
