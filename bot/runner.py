# bot/runner.py

from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import format_match
from bot.config import CONFIG
from bot.throttle import throttle
import os
import time

TOKEN = os.getenv("TOKEN")
MAX_RETRIES = 2

def process_player(player_name: str, steam_id: int, last_posted_id: str | None, state: dict) -> None:
    """
    Fetch and format the latest match for a player. Updates state if successful.
    Includes simple retry mechanism for transient failures.
    """
    retries = 0
    match_bundle = None

    while retries <= MAX_RETRIES:
        throttle()  # ✅ Enforce rate limit before each attempt
        match_bundle = get_latest_new_match(steam_id, last_posted_id, TOKEN)
        if match_bundle or retries == MAX_RETRIES:
            break
        print(f"🔁 Retry {retries + 1} for {player_name} due to fetch failure...")
        time.sleep(2)
        retries += 1

    if not match_bundle:
        print(f"⏩ No new match or failed to fetch for {player_name}. Skipping.")
        return

    match_id = match_bundle["match_id"]
    match_data = match_bundle["full_data"]
    game_mode = match_bundle.get("game_mode", "UNKNOWN")

    player_data = next(
        (p for p in match_data["players"] if p.get("steamAccountId") == steam_id),
        None
    )
    if not player_data:
        print(f"❌ Player data missing in match {match_id} for {player_name}")
        return

    hero_name = player_data.get("hero", {}).get("name", "unknown").replace("npc_dota_hero_", "")
    kills = player_data.get("kills", 0)
    deaths = player_data.get("deaths", 0)
    assists = player_data.get("assists", 0)
    won = player_data.get("isVictory", False)

    readable_mode = game_mode.title().replace("_", " ") if isinstance(game_mode, str) else f"Mode {game_mode}"

    print(f"🎮 {player_name} — {hero_name}: {kills}/{deaths}/{assists} — {'🏆 Win' if won else '💀 Loss'} (Match ID: {match_id})")
    print(f"📊 Performance Analysis:")
    print(f"🧠 Mode: {game_mode} → Using {'Turbo' if game_mode == 'TURBO' else 'Normal'} engine")

    try:
        feedback = format_match(player_name, steam_id, hero_name, kills, deaths, assists, won, match_data)
        print(feedback)
        state[str(steam_id)] = match_id
    except Exception as e:
        print(f"❌ Failed to format match for {player_name}: {e}")


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
        process_player(player_name, steam_id, last_posted_id, state)

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
