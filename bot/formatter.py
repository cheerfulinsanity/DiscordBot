# bot/formatter.py

import json
import os
from pathlib import Path
from datetime import datetime

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
    match_id = full_match.get("id")
    match_players = full_match.get("players", [])
    match_start = full_match.get("startDateTime", 0)
    match_duration = full_match.get("durationSeconds", 0)

    player = next((p for p in match_players if p["steamAccountId"] == player_id), None)
    if not player:
        return f"❌ Player data not found in match {match_id}"

    if os.getenv("DEBUG_MODE") == "1":
        print("🧪 Player Block:")
        print(json.dumps(player, indent=2))
        stats_debug = player.get("stats", {})
        print(f"🧪 Types — campStack: {type(stats_debug.get('campStack'))}, level: {type(stats_debug.get('level'))}")

    # Defensive stat extraction
    stats_block = player.get("stats")
    if not isinstance(stats_block, dict):
        stats_block = {}

    # Normalize campStack and level regardless of type
    camp_stack = stats_block.get("campStack")
    if not isinstance(camp_stack, list):
        camp_stack = [camp_stack] if camp_stack is not None else []

    level_list = stats_block.get("level")
    if not isinstance(level_list, list):
        level_list = [level_list] if level_list is not None else []

    stats = {
        'kills': player.get('kills', 0),
        'deaths': player.get('deaths', 0),
        'assists': player.get('assists', 0),
        'gpm': player.get('goldPerMinute', 0),
        'xpm': player.get('experiencePerMinute', 0),
        'imp': player.get('imp', 0),
        'campStack': sum(camp_stack),
        'level': level_list[-1] if level_list else 0,
    }

    role = get_role(hero_name)
    baseline = get_baseline(hero_name, role)
    if not baseline:
        return f"❌ No baseline for {hero_name} ({role})"

    # Score calculation
    deltas = {}
    score = 0
    weightings = {
        'kills': 1.0,
        'deaths': -1.5,
        'assists': 0.7,
        'gpm': 0.02,
        'xpm': 0.02,
        'imp': 1.0,
        'campStack': 0.5,
        'level': 0.5,
    }

    for stat, value in stats.items():
        delta = value - baseline.get(stat, 0)
        deltas[stat] = delta
        score += delta * weightings.get(stat, 1.0)

    highlight = max(deltas, key=lambda k: deltas[k]) if deltas else "N/A"
    lowlight = min(deltas, key=lambda k: deltas[k]) if deltas else "N/A"

    praises = [k for k, v in deltas.items() if v > 0]
    critiques = [k for k, v in deltas.items() if v < 0]

    compound_flags = []
    if stats['kills'] + stats['assists'] < 5:
        compound_flags.append("low_kp")
    if stats['deaths'] >= 10:
        compound_flags.append("feeder_alert")
    if stats['imp'] >= 10:
        compound_flags.append("impact_god")

    kda = f"{kills}/{deaths}/{assists}"
    win_emoji = "🏆 Win" if won else "💀 Loss"
    header = f"🧙 {player_name} — {hero_name}: {kda} — {win_emoji} (Match ID: {match_id})"
    summary = f"📈 Score: {round(score, 2)}"
    tags = f"📊 Tags: highlight={highlight} | lowlight={lowlight} | critiques={critiques} | praises={praises}"
    if compound_flags:
        tags += f" | compound_flags={compound_flags}"

    return f"{header}\n📊 Performance Analysis:\n{summary}\n{tags}"
