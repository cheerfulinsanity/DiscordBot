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

def run_bot() -> list[str]:
    if not TOKEN:
        return ["❌ TOKEN environment variable is not set."]

    config = load_config()
    players = config.get("players", {})

    results = []
    for i, (name, steam_id) in enumerate(players.items(), 1):
        try:
            match = fetch_latest_match(steam_id, TOKEN)
            result = (
                f"🧙 {name} — {match['hero_name']}: {match['kills']}/"
                f"{match['deaths']}/{match['assists']} — "
                f"{'🏆 Win' if match['won'] else '💀 Loss'} "
                f"(Match ID: {match['match_id']})"
            )
            results.append(result)

        except Exception as e:
            results.append(f"❌ {name} ({steam_id}): {e}")

        time.sleep(0.25)  # 💡 4 requests/sec = 60s / 15 burst = safe

    return results
