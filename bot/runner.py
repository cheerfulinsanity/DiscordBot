from bot.fetch import get_latest_match, get_match_details
from bot.stratz import load_hero_data, load_role_data, load_baselines
from bot.gist_state import load_state, save_state
from bot.formatter import format_match
import json
import time
import os

CONFIG = json.load(open("config.json"))
PLAYERS = CONFIG["players"]
GUILD_NAME = CONFIG.get("guild_name", "Guild")

def log_check(index, total, name, steam_id):
    print(f"🔍 [{index}/{total}] Checking {name} ({steam_id})...")

def log_skip(reason):
    print(f"⏩ {reason}")

def log_match_summary(player_name, hero_name, kills, deaths, assists, won, match_id):
    result_emoji = "🏆 Win" if won else "💀 Loss"
    print(f"🧙 {player_name} — {hero_name}: {kills}/{deaths}/{assists} — {result_emoji} (Match ID: {match_id})")

def run_bot():
    print("🚀 GuildBot started")
    print(f"👥 Loaded {len(PLAYERS)} players from config.json")
    
    known_match_ids = load_state()
    print("📥 Loaded state.json from GitHub Gist")

    heroes = load_hero_data()
    roles = load_role_data()
    baselines = load_baselines()

    for i, (name, steam_id) in enumerate(PLAYERS.items(), 1):
        log_check(i, len(PLAYERS), name, steam_id)

        latest_match = get_latest_match(steam_id)
        if not latest_match:
            log_skip("No turbo match found.")
            continue

        match_id = latest_match["id"]
        if match_id in known_match_ids:
            log_skip("No new match. Skipping.")
            continue

        match_details = get_match_details(match_id)
        if not match_details:
            log_skip("Could not fetch full match details.")
            continue

        player = match_details["player"]
        hero_id = player["hero_id"]
        hero_name = heroes.get(str(hero_id), {}).get("localized_name", "Unknown Hero")
        won = player["won"]
        kills = player["num_kills"]
        deaths = player["num_deaths"]
        assists = player["num_assists"]

        log_match_summary(name, hero_name, kills, deaths, assists, won, match_id)

        try:
            output = format_match(
                steam_id,
                hero_id,
                heroes,
                roles,
                baselines,
                hero_name,
                kills,
                deaths,
                assists,
                won,
                match_details,
            )
            if output:
                print(output)
        except Exception as e:
            print(f"❌ Failed to format match for {name}: {e}")
            continue

        known_match_ids.add(match_id)
        time.sleep(1.5)  # to respect Stratz API rate limits

    save_state(known_match_ids)
    print("✅ GuildBot run complete.")
