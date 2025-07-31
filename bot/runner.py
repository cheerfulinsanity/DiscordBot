# bot/runner.py

import os
import time
from bot.fetch import get_latest_new_match

def run_bot():
    print("🔁 Running GuildBot minimal test")

    token = os.getenv("TOKEN")
    steam_id = 84228471
    last_posted_id = None  # Replace with state.get(...) later

    match = get_latest_new_match(steam_id, last_posted_id, token)

    if match:
        print(
            f"🧙 {match['hero_name']}: {match['kills']}/"
            f"{match['deaths']}/{match['assists']} — "
            f"{'🏆 Win' if match['won'] else '💀 Loss'} "
            f"(Match ID: {match['match_id']})"
        )
    else:
        print("⏭️ No new match")

    time.sleep(1.0)  # placeholder for eventual rate limit pacing
