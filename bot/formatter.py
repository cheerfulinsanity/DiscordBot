import json
from pathlib import Path
from feedback.engine import analyze_player
from feedback.advice import generate_advice  # 🆕 Import advice generator

# Load hero baselines and roles from local JSON
baseline_path = Path(__file__).parent / "../data/hero_baselines.json"
roles_path = Path(__file__).parent / "../data/hero_roles.json"

with open(baseline_path, "r") as f:
    HERO_BASELINES = json.load(f)

with open(roles_path, "r") as f:
    HERO_ROLES = json.load(f)

# Map of Stratz gameMode IDs to readable names
GAME_MODE_NAMES = {
    1: "All Pick",
    2: "Captains Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    12: "Ability Draft",
    16: "Captains Draft",
    22: "Ranked All Pick",
    23: "Turbo"
}

def normalize_hero_name(raw_name: str) -> str:
    if raw_name.startswith("npc_dota_hero_"):
        raw_name = raw_name.replace("npc_dota_hero_", "")
    return raw_name.lower()

def get_role(hero_name):
    normalized = normalize_hero_name(hero_name)
    roles = HERO_ROLES.get(normalized, [])
    return roles[0] if roles else "unknown"

def get_baseline(hero_name, role):
    normalized = normalize_hero_name(hero_name)
    return HERO_BASELINES.get(normalized)

def format_match(player_name, player_id, hero_name, kills, deaths, assists, won, full_match):
    if not isinstance(full_match, dict):
        return f"❌ Match data was not a valid dictionary. Got: {type(full_match)}"

    match_id = full_match.get("id")
    match_players = full_match.get("players", [])
    game_mode_id = full_match.get("gameMode")
    game_mode_name = GAME_MODE_NAMES.get(game_mode_id, f"Mode {game_mode_id}")
    is_turbo = game_mode_id == 23

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

    is_radiant = player.get("isRadiant")
    team_kills = sum(p.get("kills", 0) for p in match_players if p.get("isRadiant") == is_radiant)

    try:
        ignore_stats = ["gpm", "xpm"] if is_turbo else []
        result = analyze_player(stats, baseline, role, team_kills, ignore_stats=ignore_stats)
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

    # Compose performance title
    kda = f"{kills}/{deaths}/{assists}"
    win_emoji = "🏆" if won else "💀"
    score = result['score']
    hero_display = player.get("hero", {}).get("displayName", normalize_hero_name(hero_name).title())

    if score >= 3.5:
        icon, phrase = "💨", "blew up the game"
    elif score >= 2.0:
        icon, phrase = "🔥", "went off"
    elif score >= 0.5:
        icon, phrase = "🎯", "went steady"
    elif score >= -0.5:
        icon, phrase = "🎲", "turned up"
    elif score >= -2.0:
        icon, phrase = "💀", "struggled"
    else:
        icon, phrase = "☠️", "inted it all away"

    header = f"{icon} {player_name} {phrase} {kda} as {hero_display} — {win_emoji} {'Win' if won else 'Loss'} (Match {match_id}, {game_mode_name})"
    summary = f"📊 Score: {round(score, 2)}"

    # Generate structured advice with turbo-aware exclusions
    advice = generate_advice(result['feedback_tags'], result['deltas'], ignore_stats=ignore_stats)

    advice_sections = []

    if advice["positives"]:
        advice_sections.append("🎯 What went well:")
        for line in advice["positives"]:
            advice_sections.append(f"- {line}")

    if advice["negatives"]:
        advice_sections.append("🚰 What to work on:")
        for line in advice["negatives"]:
            advice_sections.append(f"- {line}")

    if advice["flags"]:
        advice_sections.append("💼 Flagged behavior:")
        for line in advice["flags"]:
            advice_sections.append(f"- {line}")

    if advice["tips"]:
        advice_sections.append("🗾️ Tips:")
        for line in advice["tips"]:
            advice_sections.append(f"- {line}")

    return f"{header}\n📊 Performance Analysis:\n{summary}\n" + "\n".join(advice_sections)
