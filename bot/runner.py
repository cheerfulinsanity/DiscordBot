from bot.fetch import get_latest_match_id, get_match_details
from bot.gist_state import load_state, save_state
from bot.formatter import format_match
from config import CONFIG
from time import sleep
from stratz import get_steam_ids

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

        latest_match_id = get_latest_match_id(player_id)
        if latest_match_id in known_match_ids:
            print("⏩ No new match. Skipping.")
            continue

        match_data = get_match_details(latest_match_id)
        if not match_data:
            print(f"❌ Failed to fetch match data for {player_name}")
            continue

        match_players = match_data.get("players", [])
        player_data = next((p for p in match_players if p.get("steamAccountId") == player_id), None)

        if not player_data:
            print(f"❌ Player data missing in match for {player_name}")
            continue

        hero_name = player_data.get("hero", {}).get("name", "unknown")
        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        assists = player_data.get("assists", 0)
        won = player_data.get("isVictory", False)

        print(f"🧙 {player_name} — {hero_name.split('_')[-1]}: {kills}/{deaths}/{assists} — {'🏆 Win' if won else '💀 Loss'} (Match ID: {latest_match_id})")
        print("📊 Performance Analysis:")

        try:
            feedback = format_match(
                player_name,
                player_id,
                hero_name,
                kills,
                deaths,
                assists,
                won,
                match_data
            )
            print(feedback)
        except Exception as e:
            print(f"❌ Failed to format match for {player_name}: {e}")

        known_match_ids.add(latest_match_id)
        sleep(1.2)

    save_state(known_match_ids)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
