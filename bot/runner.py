# bot/runner.py

from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import format_match
from bot.config import CONFIG
from time import sleep
import os

TOKEN = os.getenv("TOKEN")

def run_bot():
    print("🚀 GuildBot started")

    players = CONFIG["players"]
    print(f"👥 Loaded {len(players)} players from config.json")

    state = load_state()
    print("📥 Loaded state.json from GitHub Gist")

    for index, (player_name, steam_id) in enumerate(players.items(), start=1):
        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({steam_id})...")

        last_posted_id = state.get(str(steam_id))
        match_bundle = get_latest_new_match(steam_id, last_posted_id, TOKEN)

        if not match_bundle:
            print("⏩ No new match or failed to fetch. Skipping.")
            continue

        match_id = match_bundle["match_id"]
        match_data = match_bundle["full_data"]

        # Try to find this player's block
        player_data = next(
            (p for p in match_data.get("players", []) if p.get("steamAccountId") == steam_id),
            None
        )

        if not player_data:
            print(f"❌ Player data missing in match {match_id}")
            continue

        hero_name = player_data.get("hero", {}).get("name", "unknown").replace("npc_dota_hero_", "")
        kills = player_data.get("kills", 0)
        deaths = player_data.get("deaths", 0)
        assists = player_data.get("assists", 0)
        won = player_data.get("isVictory", False)

        print(f"🧙 {player_name} — {hero_name}: {kills}/{deaths}/{assists} — {'🏆 Win' if won else '💀 Loss'} (Match ID: {match_id})")
        print("📊 Performance Analysis:")

        try:
            feedback = format_match(
                player_name,
                steam_id,
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

        # Update state
        state[str(steam_id)] = match_id
        sleep(1.2)

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
