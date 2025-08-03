# bot/runner.py

from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import format_match_embed, build_discord_embed
from bot.config import CONFIG
from bot.throttle import throttle
import os
import requests
import json
import time  # ✅ Added for inter-player delay

TOKEN = os.getenv("TOKEN")

def post_to_discord_embed(embed: dict, webhook_url: str) -> bool:
    payload = {"embeds": [embed]}
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 204:
            return True
        else:
            print(f"⚠️ Discord webhook responded {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to post embed to Discord: {e}")
        return False

def process_player(player_name: str, steam_id: int, last_posted_id: str | None, state: dict) -> bool:
    """
    Fetch and format the latest match for a player. Updates state if successful.
    Returns True if processing should continue, False if quota was exceeded.
    """
    throttle()  # ✅ Rate-limit before each player's call
    match_bundle = get_latest_new_match(steam_id, last_posted_id, TOKEN)

    if isinstance(match_bundle, dict) and match_bundle.get("error") == "quota_exceeded":
        print(f"🛑 Skipping remaining players — quota exceeded.")
        return False

    if not match_bundle:
        print(f"⏩ No new match or failed to fetch for {player_name}. Skipping.")
        return True

    match_id = match_bundle["match_id"]
    match_data = match_bundle["full_data"]

    player_data = next(
        (p for p in match_data["players"] if p.get("steamAccountId") == steam_id),
        None
    )
    if not player_data:
        print(f"❌ Player data missing in match {match_id} for {player_name}")
        return True

    print(f"🎮 {player_name} — processing match {match_id}")

    try:
        result = format_match_embed(player_data, match_data, player_data.get("stats", {}), player_name)
        embed = build_discord_embed(result)

        if CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
            posted = post_to_discord_embed(embed, CONFIG["webhook_url"])
            if posted:
                print(f"✅ Posted embed for {player_name} match {match_id}")
                state[str(steam_id)] = match_id
            else:
                print(f"⚠️ Failed to post embed for {player_name} match {match_id}")
        else:
            print("⚠️ Webhook disabled or misconfigured — printing instead.")
            print(json.dumps(embed, indent=2))
            state[str(steam_id)] = match_id

    except Exception as e:
        print(f"❌ Error formatting or posting match for {player_name}: {e}")

    return True

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
        should_continue = process_player(player_name, steam_id, last_posted_id, state)
        if not should_continue:
            print("🧯 Ending run early to preserve API quota.")
            break
        time.sleep(0.2)  # 🛡️ Soft cooldown between players to ease API burst pressure

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
