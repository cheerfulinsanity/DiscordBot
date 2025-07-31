from bot.fetch import get_latest_new_match, get_full_match_data
from bot.gist_state import load_state, save_state
from bot.formatter import format_match
from config import CONFIG
from time import sleep
import logging

logging.basicConfig(level=logging.INFO)

def run_bot():
    print("🚀 GuildBot started")

    players = CONFIG["players"]
    print(f"👥 Loaded {len(players)} players from config.json")

    known_match_ids = load_state()
    print("📥 Loaded state.json from GitHub Gist")

    for index, (player_name, player_id) in enumerate(players.items(), start=1):
        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({player_id})...")

        latest_match = get_latest_new_match(player_id, known_match_ids.get(str(player_id)), CONFIG["stratz_token"])
        if not latest_match:
            print("⏩ No new match. Skipping.")
            continue

        match_id = latest_match["match_id"]
        print(f"🧙 {player_name} — {latest_match['hero_name']}: {latest_match['kills']}/{latest_match['deaths']}/{latest_match['assists']} — {'🏆 Win' if latest_match['won'] else '💀 Loss'} (Match ID: {match_id})")
        print("📊 Performance Analysis:")

        match_data = get_full_match_data(player_id, match_id, CONFIG["stratz_token"])
        if not match_data:
            print(f"❌ Failed to fetch full match for {player_name}")
            continue

        try:
            feedback = format_match(
                player_name,
                player_id,
                latest_match["hero_name"],
                latest_match["kills"],
                latest_match["deaths"],
                latest_match["assists"],
                latest_match["won"],
                match_data
            )
            print(feedback)
        except Exception as e:
            print(f"❌ Failed to format match for {player_name}: {e}")

        known_match_ids[str(player_id)] = match_id
        sleep(1.2)

    save_state(known_match_ids)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
