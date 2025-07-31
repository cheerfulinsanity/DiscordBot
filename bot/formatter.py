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
    RAW_BASELINES = json.load(f)

# Reformat baselines into dict[hero][role]
HERO_BASELINES = {}
for entry in RAW_BASELINES:
    hero = entry["hero"]
    if hero not in HERO_BASELINES:
        HERO_BASELINES[hero] = {}
    for role in HERO_ROLES.get(hero, ["unknown"]):
        HERO_BASELINES[hero][role] = {
            k: entry[k] for k in ["kills", "deaths", "assists", "gpm", "xpm"]
            if k in entry
        }

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

    stats = {
        'kills': player.get('kills', 0),
        'deaths': player.get('deaths', 0),
        'assists': player.get('assists', 0),
        'gpm': player.get('goldPerMinute', 0),
        'xpm': player.get('experiencePerMinute', 0),
        'imp': player.get('imp', 0),
        'campStack': sum(player.get("stats", {}).get("campStack", [])) if isinstance(player.get("stats", {}).get("campStack"), list) else 0,
        'level': player.get("stats", {}).get("level", [-1])[-1] if isinstance(player.get("stats", {}).get("level"), list) else 0,
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
