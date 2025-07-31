# bot/runner.py

from bot.fetch import get_latest_new_match, get_full_match_data
from bot.formatter import format_match
from bot.gist_state import load_state, update_state
from bot.opendota import get_hero_name
from bot.config import load_config
import time

def run_bot():
    print("🚀 GuildBot started")

    config = load_config()
    print(f"👥 Loaded {len(config)} players from config.json")

    state = load_state()
    print("📥 Loaded state.json from GitHub Gist")

    token = state.get("stratz_token")
    if not token:
        print("❌ No Stratz API token found in state.json. Aborting.")
        return

    for idx, player in enumerate(config):
        name = player["name"]
        steam_id = player["steam_id"]
        last_match_id = state.get("last_match_ids", {}).get(str(steam_id))

        print(f"🔍 [{idx+1}/{len(config)}] Checking {name} ({steam_id})...")

        try:
            match = get_latest_new_match(steam_id, last_match_id, token)
        except Exception as e:
            print(f"⚠️  Failed to fetch latest match for {name}: {e}")
            continue

        if not match:
            print("⏩ No new match. Skipping.")
            continue

        hero_name = get_hero_name(match["hero_id"])
        won = match["won"]
        kills = match["kills"]
        deaths = match["deaths"]
        assists = match["assists"]
        match_id = match["match_id"]

        outcome_emoji = "🏆 Win" if won else "💀 Loss"
        print(f"🧙 {name} — {hero_name}: {kills}/{deaths}/{assists} — {outcome_emoji} (Match ID: {match_id})")

        print("📊 Performance Analysis:")
        try:
            full_match = get_full_match_data(steam_id, match_id, token)
            print(format_match(name, hero_name, kills, deaths, assists, won, full_match))
        except Exception as e:
            print(f"❌ Failed to format match for {name}: {e}")

        state["last_match_ids"][str(steam_id)] = match_id
        time.sleep(1)

    update_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
