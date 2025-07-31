# bot/formatter.py

import json
from pathlib import Path
from feedback.engine import analyze_player

# Load hero roles and baselines
roles_path = Path(__file__).parent / "../data/hero_roles.json"
baselines_path = Path(__file__).parent / "../data/hero_baselines.json"

with open(roles_path, "r") as f:
    HERO_ROLES = json.load(f)

with open(baselines_path, "r") as f:
    HERO_BASELINES = json.load(f)


def get_role(hero_name: str) -> str:
    roles = HERO_ROLES.get(hero_name, [])
    if not roles:
        return "unknown"
    for r in roles:
        if "support" in r:
            return "support"
    return "core"


def get_baseline(hero_name: str, role: str) -> dict:
    return HERO_BASELINES.get(hero_name, {}).get(role)


def format_match(player_name, player_id, hero_name, kills, deaths, assists, won, full_match):
    match_id = full_match.get("id")
    player = next((p for p in full_match.get("players", []) if p["steamAccountId"] == player_id), None)
    if not player:
        return f"❌ Player data not found in match {match_id}"

    stats_block = player.get("stats", {})

    # Safely handle scalar or list cases
    camp_stack_raw = stats_block.get("campStack", 0)
    if isinstance(camp_stack_raw, list):
        camp_stack = sum(camp_stack_raw)
    else:
        camp_stack = camp_stack_raw or 0

    level_raw = stats_block.get("level", 0)
    if isinstance(level_raw, list):
        level = level_raw[-1] if level_raw else 0
    else:
        level = level_raw or 0

    stats = {
        'kills': player.get('kills', 0),
        'deaths': player.get('deaths', 0),
        'assists': player.get('assists', 0),
        'gpm': player.get('goldPerMinute', 0),
        'xpm': player.get('experiencePerMinute', 0),
        'imp': player.get('imp', 0),
        'campStack': camp_stack,
        'level': level,
    }

    role = get_role(hero_name)
    baseline = get_baseline(hero_name, role)
    if not baseline:
        return f"❌ No baseline available for {hero_name} ({role})"

    team_kills = sum(p.get("kills", 0) for p in full_match.get("players", []) if p.get("isRadiant") == player.get("isRadiant"))

    result = analyze_player(stats, baseline, role, team_kills)
    feedback = result["feedback_tags"]

    kda = f"{kills}/{deaths}/{assists}"
    win_emoji = "🏆 Win" if won else "💀 Loss"
    header = f"🧙 {player_name} — {hero_name}: {kda} — {win_emoji} (Match ID: {match_id})"
    summary = f"📈 Score: {round(result['score'], 2)}"
    tags = (
        f"📊 Tags: highlight={feedback['highlight']} | lowlight={feedback['lowlight']} | "
        f"critiques={feedback['critiques']} | praises={feedback['praises']}"
    )
    if feedback['compound_flags']:
        tags += f" | compound_flags={feedback['compound_flags']}"

    return f"{header}\n📊 Performance Analysis:\n{summary}\n{tags}"
