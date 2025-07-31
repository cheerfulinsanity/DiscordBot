# runner.py

import os
import json
from bot.fetch import get_latest_new_match, get_full_match_data
from feedback.engine import analyze_player
from bot.gist_state import load_state, save_state
from data.config import load_config
from data.hero_baselines import get_hero_baseline
from data.hero_roles import get_expected_role

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

        hero_short = player['hero']['name'].replace("npc_dota_hero_", "")
        role = get_expected_role(hero_short)
        baseline = get_hero_baseline(hero_short, role)

        if not baseline:
            print("⚠️ No baseline found. Skipping feedback.")
            continue

        analysis = analyze_player(stats, baseline, role, team_kills)

        print("📊 Feedback Tags:")
        print(json.dumps(analysis['feedback_tags'], indent=2))

        print("📈 Score:", analysis['score'])

        summary = "🧠 Performance summary: "
        if analysis['feedback_tags'].get("compound_flags"):
            summary += f"🔺 Compound issue: {analysis['feedback_tags']['compound_flags'][0]}"
        elif analysis['feedback_tags'].get("critiques"):
            summary += f"🔻 Critique: {analysis['feedback_tags']['critiques'][0]}"
        elif analysis['feedback_tags'].get("praises"):
            summary += f"🌟 Praise: {analysis['feedback_tags']['praises'][0]}"
        else:
            summary += "🤷 No strong signals detected."

        print(summary)

        # Update state to prevent repost
        state[str(steam_id)] = latest['match_id']

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
