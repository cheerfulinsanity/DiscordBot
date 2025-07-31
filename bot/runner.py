# runner.py

import os
from bot.fetch import get_latest_new_match, get_full_match_data
from feedback.engine import analyze_player
from data.config import load_config
from bot.gist_state import load_state, save_state

# Temporary import for printing/logging output
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

        # Extract stats for feedback
        team_kills = sum(p['kills'] for p in full_data['players'] if p['isRadiant'] == player['isRadiant'])

        stats = {
            'kills': player['kills'],
            'deaths': player['deaths'],
            'assists': player['assists'],
            'gpm': player['goldPerMinute'],
            'xpm': player['experiencePerMinute'],
            'imp': player['imp'],
            'campStack': sum(player['stats'].get('campStack') or []),
            'level': max(player['stats'].get('level') or [0])
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

        print("📊 Feedback Score: {:.2f}".format(analysis['score']))
        if analysis['praise']:
            print("🌟 Praise:")
            for line in analysis['praise']:
                print("   👍", line)
        if analysis['advice']:
            print("🛠️ Advice:")
            for line in analysis['advice']:
                print("   ⚠️", line)

        # Optional: top-level summary message
        if analysis['score'] > 0.4:
            summary = "💪 Clean game! Strong numbers and good impact."
        elif analysis['score'] > 0.15:
            summary = "👌 Solid showing. A few tweaks and you’re golden."
        elif analysis['score'] > -0.15:
            summary = "🤔 Mixed bag. Some good moves, some head-scratchers."
        else:
            summary = "🫠 Statistically a war crime. Time for a review session."

        print(f"🧠 Summary: {summary}")

        # Update state to prevent repost
        state[str(steam_id)] = latest['match_id']

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
