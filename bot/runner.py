# runner.py

import os
from bot.fetch import get_latest_new_match, get_full_match_data
from feedback.engine import analyze_player
from data.config import load_config
from bot.gist_state import load_state, save_state

import json

TOKEN = os.getenv("TOKEN")

def run():
    config = load_config()
    state = load_state()

    print("🚀 GuildBot started")
    print(f"👥 Loaded {len(config)} players from config.json")

    for name, steam_id in config.items():
        print(f"🔍 Checking {name} ({steam_id})...")

        latest = get_latest_new_match(steam_id, state, TOKEN)
        if not latest:
            print("⏩ No new match. Skipping.")
            continue

        print(f"🧙 {name} — {latest['hero_name']}: {latest['kills']}/{latest['deaths']}/{latest['assists']} — {'🏆 Win' if latest['won'] else '💀 Loss'} (Match ID: {latest['match_id']})")

        full_data = get_full_match_data(steam_id, latest['match_id'], TOKEN)
        if not full_data:
            print("⚠️ Full match fetch failed")
            continue

        player = next((p for p in full_data['players'] if p['steamAccountId'] == steam_id), None)
        if not player:
            print("⚠️ Player not found in match")
            continue

        team_kills = sum(p['kills'] for p in full_data['players'] if p['isRadiant'] == player['isRadiant'])

        stats = {
            'kills': player['kills'],
            'deaths': player['deaths'],
            'assists': player['assists'],
            'gpm': player['goldPerMinute'],
            'xpm': player['experiencePerMinute'],
            'imp': player['imp'],
            'campStack': sum(player['stats'].get('campStack', [])),
            'level': player['stats'].get('level', [])[-1] if player['stats'].get('level') else 0,
        }

        from data.hero_baselines import get_hero_baseline
        from data.hero_roles import get_expected_role

        hero_short = player['hero']['name'].replace("npc_dota_hero_", "")
        role = get_expected_role(hero_short)
        baseline = get_hero_baseline(hero_short, role)

        if not baseline:
            print("⚠️ No baseline found. Skipping feedback.")
            continue

        analysis = analyze_player(stats, baseline, role, team_kills)

        print("📊 Feedback Analysis:")
        for key, val in analysis.items():
            if isinstance(val, dict):
                print(f"{key}:")
                for subkey, subval in val.items():
                    print(f"  {subkey}: {subval}")
            else:
                print(f"{key}: {val}")

        top_tag = analysis['feedback_tags'].get('compound_flags') or analysis['feedback_tags'].get('critiques')
        summary_line = "🧠 Performance review: "
        if top_tag:
            summary_line += f"Most notable issue: {top_tag[0]}"
        elif analysis['score'] > 0.2:
            summary_line += "Great game! Solid stats across the board."
        elif analysis['score'] < -0.3:
            summary_line += "Rough one. Stats say: time to hit the demo range."
        else:
            summary_line += "Decent showing — but plenty of room to improve."

        print(summary_line)

        state[str(steam_id)] = latest['match_id']

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
