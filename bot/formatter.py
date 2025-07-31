# bot/formatter.py

import json
from pathlib import Path
from datetime import datetime
from feedback.engine import analyze_player

# Load hero baselines and roles inline from local JSON
baseline_path = Path(__file__).parent / "../data/hero_baselines.json"
roles_path = Path(__file__).parent / "../data/hero_roles.json"

with open(baseline_path, "r") as f:
    HERO_BASELINES = json.load(f)

with open(roles_path, "r") as f:
    HERO_ROLES = json.load(f)


def get_role(hero_name):
    return HERO_ROLES.get(hero_name, "unknown")


def get_baseline(hero_name, role):
    return HERO_BASELINES.get(hero_name, {}).get(role)


def format_match(player_name, player_id, hero_name, kills, deaths, assists, won, full_match):
    if not isinstance(full_match, dict):
        return f"❌ Match data was not a valid dictionary. Got: {type(full_match)}"

    match_id = full_match.get("id")
    match_players = full_match.get("players", [])

    if not isinstance(match_players, list):
        return f"❌ 'players' field is not a list. Got: {type(match_players)}"

    for p in match_players:
        if not isinstance(p, dict):
            return f"❌ Malformed player entry in match {match_id}: expected dict, got {type(p)}"

    player = next((p for p in match_players if p.get("steamAccountId") == player_id), None)
    if not player:
        return f"❌ Player data not found in match {match_id}"

    stats_block = player.get("stats") or {}
    if not isinstance(stats_block, dict):
        return f"❌ 'stats' field is not a dict. Got: {type(stats_block)}"

    camp_stack = stats_block.get("campStack") or []
    level_list = stats_block.get("level") or []

    stats = {
        'kills': player.get('kills', 0),
        'deaths': player.get('deaths', 0),
        'assists': player.get('assists', 0),
        'gpm': player.get('goldPerMinute', 0),
        'xpm': player.get('experiencePerMinute', 0),
        'imp': player.get('imp') if player.get('imp') is not None else 0,
        'campStack': sum(camp_stack) if isinstance(camp_stack, list) else 0,
        'level': level_list[-1] if isinstance(level_list, list) and level_list else 0,
    }

    role = get_role(hero_name)
    baseline = get_baseline(hero_name, role)
    if not baseline:
        return f"❌ No baseline for {hero_name} ({role})"

    # Compute team kills for kill participation
    is_radiant = player.get("isRadiant")
    team_kills = sum(
        p.get("kills", 0) for p in match_players
        if p.get("isRadiant") == is_radiant
    )

    try:
        result = analyze_player(stats, baseline, role, team_kills)
    except Exception as e:
        debug_dump = {
            "player_name": player_name,
            "hero_name": hero_name,
            "stats": stats,
            "baseline": baseline,
            "role": role,
            "team_kills": team_kills
        }
        return f"❌ analyze_player raised error for {player_name}: {e}\n🧪 Debug dump:\n{json.dumps(debug_dump, indent=2)}"

    # Output summary log
    kda = f"{kills}/{deaths}/{assists}"
    win_emoji = "🏆 Win" if won else "💀 Loss"
    header = f"🧙 {player_name} — {hero_name.split('_')[-1]}: {kda} — {win_emoji} (Match ID: {match_id})"
    summary = f"📈 Score: {round(result['score'], 2)}"

    tags = result['feedback_tags']
    tag_line = f"📊 Tags: highlight={tags['highlight']} | lowlight={tags['lowlight']} | critiques={tags['critiques']} | praises={tags['praises']}"
    if tags.get("compound_flags"):
        tag_line += f" | compound_flags={tags['compound_flags']}"

    return f"{header}\n📊 Performance Analysis:\n{summary}\n{tag_line}"
