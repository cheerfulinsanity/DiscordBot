import os
import json
from bot.fetch import get_latest_new_match, get_full_match_data
from bot.formatter import format_match
from feedback.engine import analyze_player
from bot.gist_state import load_state, save_state

def run_bot():
    print("🚀 GuildBot started")

    # Load config.json directly
    with open("config.json", "r") as f:
        config = json.load(f)
    print(f"👥 Loaded {len(config)} players from config.json")

    state = load_state()
    print("📥 Loaded state.json from GitHub Gist")

    new_state = {}
    for i, (player_name, steam_id) in enumerate(config.items(), start=1):
        print(f"🔍 [{i}/{len(config)}] Checking {player_name} ({steam_id})...")

        latest = get_latest_new_match(steam_id, state.get(str(steam_id)))
        if not latest:
            print("⏩ No new match. Skipping.")
            new_state[str(steam_id)] = state.get(str(steam_id))
            continue

        print(f"🧙 {player_name} — {latest['hero_name']}: {latest['kills']}/{latest['deaths']}/{latest['assists']} — {'🏆 Win' if latest['won'] else '💀 Loss'} (Match ID: {latest['match_id']})")

        match_data = get_full_match_data(steam_id, latest["match_id"])
        if not match_data:
            print("⚠️ Full match fetch failed")
            continue

        # Run feedback analysis
        feedback = analyze_player(match_data)
        print(f"💬 Feedback tokens: {feedback}")

        # Format and (later) send match summary
        message = format_match(player_name, latest, match_data)
        print(message)  # currently logging to console

        new_state[str(steam_id)] = latest["match_id"]

    save_state(new_state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
