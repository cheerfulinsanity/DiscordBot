import json
from pathlib import Path
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from datetime import datetime

# --- Canonical stat sets ---
NORMAL_STATS = ["gpm", "xpm", "imp", "kills", "deaths", "assists", "campStack", "level", "killParticipation"]
TURBO_STATS  = ["imp", "kills", "deaths", "assists", "campStack", "level", "killParticipation"]

# --- Paths ---
BASELINES_NORMAL_PATH = Path(__file__).parent / "../data/hero_baselines.json"
BASELINES_TURBO_PATH  = Path(__file__).parent / "../data/hero_baselines_turbo.json"
ROLES_PATH            = Path(__file__).parent / "../data/hero_roles.json"

# --- Data loads ---
with open(BASELINES_NORMAL_PATH, "r") as f:
    HERO_BASELINES_NORMAL = json.load(f)

with open(BASELINES_TURBO_PATH, "r") as f:
    HERO_BASELINES_TURBO = json.load(f)

with open(ROLES_PATH, "r") as f:
    HERO_ROLES = json.load(f)

# --- Game mode map ---
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

# --- Utility functions ---
def normalize_hero_name(raw_name: str) -> str:
    if raw_name.startswith("npc_dota_hero_"):
        raw_name = raw_name.replace("npc_dota_hero_", "")
    return raw_name.lower()

def get_role(hero_name: str) -> str:
    normalized = normalize_hero_name(hero_name)
    roles = HERO_ROLES.get(normalized, [])
    return roles[0] if roles else "unknown"

def get_baseline(hero_name: str, mode: str) -> dict | None:
    normalized = normalize_hero_name(hero_name)
    if mode == "TURBO":
        return HERO_BASELINES_TURBO.get(normalized)
    return HERO_BASELINES_NORMAL.get(normalized)

def _extract_stats(player: dict, stats_block: dict, stat_keys: list[str]) -> dict:
    stats = {}
    for key in stat_keys:
        if key == "campStack":
            camp_stack = stats_block.get("campStack") or []
            stats["campStack"] = sum(camp_stack) if isinstance(camp_stack, list) else 0
        elif key == "level":
            level_list = stats_block.get("level") or []
            stats["level"] = level_list[-1] if isinstance(level_list, list) and level_list else 0
        else:
            stats[key] = player.get(key, 0)
    return stats

# --- Main plain text formatter ---
def format_match(player_name, player_id, hero_name, kills, deaths, assists, won, full_match):
    if not isinstance(full_match, dict):
        return f"❌ Match data was not a valid dictionary. Got: {type(full_match)}"

    match_id = full_match.get("id")
    match_players = full_match.get("players", [])
    game_mode_str = str(full_match.get("gameMode", "")).upper()

    if not isinstance(match_players, list):
        return f"❌ 'players' field is not a list. Got: {type(match_players)}"

    if not game_mode_str:
        return f"❌ Missing gameMode field in match {match_id}"

    is_turbo = game_mode_str == "TURBO"
    mode_flag = "TURBO" if is_turbo else "NON_TURBO"
    game_mode_name = game_mode_str.title()
    stat_keys = TURBO_STATS if is_turbo else NORMAL_STATS

    player = next((p for p in match_players if p.get("steamAccountId") == player_id), None)
    if not player:
        return f"❌ Player data not found in match {match_id}"

    stats_block = player.get("stats") or {}
    if not isinstance(stats_block, dict):
        return f"❌ 'stats' field is not a dict. Got: {type(stats_block)}"

    is_radiant = player.get("isRadiant", True)
    team_kills = sum(p.get("kills", 0) for p in match_players if p.get("isRadiant") == is_radiant)

    role = get_role(hero_name)
    baseline = get_baseline(hero_name, mode_flag)
    if not baseline:
        return f"❌ No baseline for {hero_name} ({role})"

    raw_stats = _extract_stats(player, stats_block, stat_keys)

    print(f"🧠 Mode: {mode_flag} → Using {'Turbo' if is_turbo else 'Normal'} engine")

    try:
        assert set(raw_stats.keys()).issubset(set(stat_keys)), f"❌ Stat leak: {raw_stats.keys()} vs {stat_keys}"
        analyze = analyze_turbo if is_turbo else analyze_normal
        result = analyze(raw_stats, baseline, role, team_kills)
    except Exception as e:
        debug_dump = {
            "player_name": player_name,
            "hero_name": hero_name,
            "stats": raw_stats,
            "baseline": baseline,
            "role": role,
            "team_kills": team_kills
        }
        return f"❌ analyze_player raised error for {player_name}: {e}\n🧪 Debug dump:\n{json.dumps(debug_dump, indent=2)}"

    # --- Formatting output ---
    kda = f"{kills}/{deaths}/{assists}"
    win_emoji = "🏆" if won else "💀"
    score = result["score"]
    hero_display = player.get("hero", {}).get("displayName") or normalize_hero_name(hero_name).title()

    # Use new helper for title emoji and phrase based on score, won, and compound flags
    icon, phrase = get_title_phrase(score, won, result["feedback_tags"].get("compound_flags", []))

    header = f"{icon} {player_name} {phrase} {kda} as {hero_display} — {win_emoji} {'Win' if won else 'Loss'} (Match {match_id}, {game_mode_name})"
    summary = f"📊 Score: {round(score, 2)}"

    ignore_stats = ["gpm", "xpm"] if is_turbo else []
    advice = generate_advice(result["feedback_tags"], result["deltas"], ignore_stats=ignore_stats, mode=mode_flag)

    advice_sections = []

    if advice["positives"]:
        advice_sections.append("🎯 What went well:")
        advice_sections.extend(f"- {line}" for line in advice["positives"])

    if advice["negatives"]:
        advice_sections.append("🚰 What to work on:")
        advice_sections.extend(f"- {line}" for line in advice["negatives"])

    if advice["flags"]:
        advice_sections.append("💼 Flagged behavior:")
        advice_sections.extend(f"- {line}" for line in advice["flags"])

    if advice["tips"]:
        advice_sections.append("🗾️ Tips:")
        advice_sections.extend(f"- {line}" for line in advice["tips"])

    return f"{header}\n📊 Performance Analysis:\n{summary}\n" + "\n".join(advice_sections)

# --- New embed formatter ---

def format_match_embed(player_name, player_id, hero_name, kills, deaths, assists, won, full_match):
    """
    Format a Discord embed dict for the match summary with rich layout.
    """
    match_id = full_match.get("id")
    match_players = full_match.get("players", [])
    game_mode_num = full_match.get("gameMode", 0)
    game_mode_str = str(game_mode_num)
    duration_seconds = full_match.get("durationSeconds") or full_match.get("duration") or 0
    duration_str = f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds else "Unknown"

    # Extract timestamp for embed (try ISO8601 string or convert from unix)
    timestamp_iso = full_match.get("startDateTime") or full_match.get("startTime") or None
    if timestamp_iso:
        try:
            ts = int(timestamp_iso)
            timestamp_iso = datetime.utcfromtimestamp(ts).isoformat() + "Z"
        except Exception:
            # if already ISO8601 string, keep it as is
            pass

    is_turbo = game_mode_str == "23" or game_mode_str.upper() == "TURBO"
    mode_flag = "TURBO" if is_turbo else "NON_TURBO"
    stat_keys = TURBO_STATS if is_turbo else NORMAL_STATS
    game_mode_name = GAME_MODE_NAMES.get(game_mode_num, f"Mode {game_mode_num}")

    player = next((p for p in match_players if p.get("steamAccountId") == player_id), None)
    if not player:
        return {"title": "Error", "description": f"Player data not found in match {match_id}"}

    stats_block = player.get("stats") or {}
    if not isinstance(stats_block, dict):
        return {"title": "Error", "description": f"'stats' field is not a dict in match {match_id}"}

    is_radiant = player.get("isRadiant", True)
    team_kills = sum(p.get("kills", 0) for p in match_players if p.get("isRadiant") == is_radiant)

    role = get_role(hero_name)
    baseline = get_baseline(hero_name, mode_flag)
    if not baseline:
        return {"title": "Error", "description": f"No baseline for {hero_name} ({role})"}

    raw_stats = _extract_stats(player, stats_block, stat_keys)
    analyze = analyze_turbo if is_turbo else analyze_normal
    result = analyze(raw_stats, baseline, role, team_kills)
    score = result["score"]

    ignore_stats = ["gpm", "xpm"] if is_turbo else []
    advice = generate_advice(result["feedback_tags"], result["deltas"], ignore_stats=ignore_stats, mode=mode_flag)

    hero_display = player.get("hero", {}).get("displayName") or normalize_hero_name(hero_name).title()
    kda = f"{kills}/{deaths}/{assists}"
    win_emoji = "🏆" if won else "💀"

    icon, phrase = get_title_phrase(score, won, result["feedback_tags"].get("compound_flags", []))

    title = f"{icon} {player_name} {phrase} {kda} as {hero_display} {win_emoji} {'Win' if won else 'Loss'}"
    color = 0x00FF00 if won else 0xFF0000

    # Format stat deltas string
    stat_lines = []
    for stat, delta in sorted(result["deltas"].items(), key=lambda x: abs(x[1]), reverse=True):
        percent = delta * 100
        sign = "+" if percent > 0 else ""
        stat_lines.append(f"{stat.upper()}: {sign}{percent:.0f}%")
    stat_deltas_str = "\n".join(stat_lines) if stat_lines else "N/A"

    def format_section(title_emoji, lines):
        if not lines:
            return None
        limited = lines[:4]  # Limit to 4 lines max per section
        return f"{title_emoji} " + "\n".join(f"• {line}" for line in limited)

    positives = format_section("🎯 What went well", advice["positives"])
    negatives = format_section("🚰 What to work on", advice["negatives"])
    flags = format_section("💼 Flagged behavior", advice["flags"])
    tips = format_section("🗾️ Tip", advice["tips"])

    fields = [
        {"name": "📊 Score", "value": f"{score:.2f}", "inline": True},
        {"name": "🎭 Role", "value": role.title(), "inline": True},
        {"name": "🎮 Mode", "value": game_mode_name, "inline": True},
        {"name": "🕐 Duration", "value": duration_str, "inline": True},
        {"name": "📈 Stat Deltas", "value": f"```{stat_deltas_str}```", "inline": False}
    ]

    for sec in (positives, negatives, flags, tips):
        if sec:
            fields.append({"name": "\u200B", "value": sec, "inline": False})

    embed = {
        "title": title,
        "color": color,
        "fields": fields,
        "footer": {"text": f"Match ID: {match_id}"},
        "timestamp": timestamp_iso
    }

    return embed
