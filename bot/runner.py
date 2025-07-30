import os
import json
import time
from bot.stratz import fetch_recent_match
from bot.formatter import format_match_summary
from bot.gist_state import load_state, save_state
from data.config import CONFIG

def run_bot():
    print("🤖 Starting GuildBot...\n")
    config = CONFIG
    state = load_state()

    for player in config["players"]:
        name = player["name"]
        steam_id = player["steam_id"]
        print(f"🔍 Checking recent match for {name}...")

        try:
            match = fetch_recent_match(steam_id)
        except Exception as e:
            print(f"⚠️ Failed to fetch match for {name}: {e}")
            continue

        match_id = match.get("match_id")
        if not match_id:
            print(f"⚠️ No match ID for {name}, skipping.")
            continue

        if str(match_id) == str(state.get(str(steam_id))):
            print(f"⏭️ Skipping {name} — already posted")
            continue

        try:
            message = format_match_summary(name, match)
        except Exception as e:
            print(f"⚠️ Failed to format match for {name}: {e}")
            continue

        # Send message to Discord or test print
        if config["test_mode"]:
            print("\n" + message + "\n")
        else:
            import requests
            webhook_url = config["webhook_url"]
            response = requests.post(
                webhook_url,
                json={"content": message},
                headers={"Content-Type": "application/json"},
            )
            if response.status_code != 204:
                print(f"⚠️ Failed to send to Discord: {response.text}")
                continue

        state[str(steam_id)] = match_id
        time.sleep(2)  # Throttle to avoid Discord 429
        print(f"✅ Posted match for {name}")

    save_state(state)
    print("\n✅ Done.\n")
