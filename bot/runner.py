# bot/runner.py

from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import format_match
from bot.config import CONFIG
from time import sleep, time
from collections import deque
import os

TOKEN = os.getenv("TOKEN")

# --- Throttle Logic ---
api_calls = deque()

MAX_CALLS_PER_SECOND = 20
MAX_CALLS_PER_MINUTE = 250
MAX_CALLS_PER_HOUR = 2000
MAX_CALLS_PER_DAY = 10000

def throttle():
    now = time()

    # Prune expired entries (older than 1 day)
    while api_calls and now - api_calls[0] > 86400:
        api_calls.popleft()

    # Count active windows
    count_1s   = sum(1 for t in api_calls if now - t <= 1)
    count_60s  = sum(1 for t in api_calls if now - t <= 60)
    count_3600 = sum(1 for t in api_calls if now - t <= 3600)

    # Back off if limits hit
    if count_1s >= MAX_CALLS_PER_SECOND:
        sleep(0.05)
        return throttle()
    if count_60s >= MAX_CALLS_PER_MINUTE:
        sleep(1)
        return throttle()
    if count_3600 >= MAX_CALLS_PER_HOUR:
        sleep(5)
        return throttle()
    if len(api_calls) >= MAX_CALLS_PER_DAY:
        raise RuntimeError("🛑 Daily Stratz API limit reached (10,000 calls)")

    api_calls.append(now)

# --- Bot Execution ---
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

        player_data = next(
            (p for p in match_data["players"] if p.get("steamAccountId") == steam_id),
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
        game_mode_id = match_data.get("gameMode", 0)
        mode_label = "TURBO" if game_mode_id == 23 else "NORMAL"
        mode_emoji = "⚡" if mode_label == "TURBO" else "🎮"

        print(f"{mode_emoji} {player_name} — {hero_name}: {kills}/{deaths}/{assists} — {'🏆 Win' if won else '💀 Loss'} (Match ID: {match_id}, Mode: {mode_label})")
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

        state[str(steam_id)] = match_id
        sleep(1.2)

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
