import json
from bot import fetch
from bot import formatter
from bot import opendota
from bot import gist_state
from feedback import engine
from data import config

def run_guildbot():
    print("🚀 GuildBot started")

    players = config.load_player_config()
    print(f"👥 Loaded {len(players)} players from config.json")

    state = gist_state.load_state()
    print(f"🧪 Gist file keys: {list(state.keys())}")
    print("📥 Loaded state.json from GitHub Gist")

    new_state = {}

    for idx, (name, steam_id) in enumerate(players.items(), 1):
        print(f"🔍 [{idx}/{len(players)}] Checking {name} ({steam_id})...")

        last_match_id = state.get(str(steam_id))
        latest_match_id = opendota.get_latest_match_id(steam_id)

        if not latest_match_id or str(latest_match_id) == str(last_match_id):
            print("⏩ No new match or failed to fetch. Skipping.")
            new_state[str(steam_id)] = last_match_id
            continue

        match = fetch.get_full_match_data(latest_match_id)
        if not match:
            print("❌ Failed to fetch full match data. Skipping.")
            continue

        player_data = next((p for p in match["players"] if p["steamAccountId"] == steam_id), None)
        if not player_data:
            print(f"❌ Could not find player {steam_id} in match. Skipping.")
            continue

        print(f"🧙 {name} — {player_data['hero']['name'].replace('npc_dota_hero_', '')}: {player_data['kills']}/{player_data['deaths']}/{player_data['assists']} — {'🏆 Win' if player_data['isVictory'] else '💀 Loss'} (Match ID: {match['id']})")

        try:
            summary = formatter.format_match_summary(match, steam_id)
            feedback = engine.generate_feedback(match, steam_id)
            print("📊 Performance Analysis:")
            print(feedback)
        except Exception as e:
            print(f"❌ Failed to format match for {name}: {e}")
            continue

        new_state[str(steam_id)] = match["id"]

    gist_state.save_state(new_state)
    print("✅ GuildBot run complete.")
