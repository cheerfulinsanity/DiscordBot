# bot/runner.py

import os
import json
import time
from bot.fetch import get_latest_new_match, get_full_match_data
from bot.gist_state import load_state, save_state

CONFIG_PATH = "data/config.json"
TOKEN = os.getenv("TOKEN")

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_bot():
    print("🚀 GuildBot started")

    if not TOKEN:
        print("❌ TOKEN is missing!")
        return

    try:
        config = load_config()
        players = config.get("players", {})
        print(f"👥 Loaded {len(players)} players from config.json")

        try:
            state = load_state()
            print("📥 Loaded state.json from GitHub Gist")
        except Exception as e:
            print(f"⚠️ Failed to load state.json: {e}")
            state = {}

        updated_state = state.copy()

        for i, (name, steam_id) in enumerate(players.items(), 1):
            print(f"\n🔍 [{i}/{len(players)}] Checking {name} ({steam_id})...")
            last_id = state.get(str(steam_id))

            try:
                match = get_latest_new_match(steam_id, last_id, TOKEN)

                if not match:
                    print("⏩ No new match. Skipping.")
                    continue

                print(
                    f"🧙 {name} — {match['hero_name']}: {match['kills']}/"
                    f"{match['deaths']}/{match['assists']} — "
                    f"{'🏆 Win' if match['won'] else '💀 Loss'} "
                    f"(Match ID: {match['match_id']})"
                )

                # Fetch and log full match payload
                full_data = get_full_match_data(steam_id, match["match_id"], TOKEN)
                if full_data:
                    print(json.dumps(full_data, indent=2))
                else:
                    print("⚠️ Full match fetch failed")

                updated_state[str(steam_id)] = match["match_id"]

            except Exception as e:
                print(f"❌ Error fetching match for {name}: {e}")

            time.sleep(0.25)  # Respect API rate limits

        try:
            save_state(updated_state)
            print("📝 Updated state.json on GitHub Gist")
        except Exception as e:
            print(f"⚠️ Failed to save state.json: {e}")

        print("\n✅ GuildBot run complete.")

    except Exception as outer:
        print(f"💥 CRASH in run_bot(): {outer}")
