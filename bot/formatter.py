import json
from pathlib import Path
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats
from datetime import datetime
import os

# --- Canonical stat sets (reference only) ---
NORMAL_STATS = [
    "kills", "deaths", "assists", "imp", "level",
    "gold", "goldSpent", "gpm", "xpm",
    "heroHealing", "heroDamage", "towerDamage", "buildingDamage", "damageTaken",
    "actionsPerMinute", "killParticipation", "fightParticipationPercent",
    "stunDuration", "disableDuration",
    "runePickups", "wardsPlaced", "sentryWardsPlaced", "observerWardsPlaced", "wardsDestroyed",
    "campStack", "neutralKills", "laneCreeps", "jungleCreeps",
    "networth", "networthPerMinute", "experiencePerMinute"
]

TURBO_STATS = [
    stat for stat in NORMAL_STATS
    if stat not in {"gpm", "xpm", "gold", "goldSpent", "networth", "networthPerMinute"}
]

# --- Game mode map (reference only) ---
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

# --- Utility: Normalize hero name from full name string ---
def normalize_hero_name(raw_name: str) -> str:
    if not raw_name:
        return "unknown"
    if raw_name.startswith("npc_dota_hero_"):
        return raw_name.replace("npc_dota_hero_", "").lower()
    return raw_name.lower()

# --- Deprecated fallback functions ---
def get_role(hero_name: str) -> str:
    return "unknown"

def get_baseline(hero_name: str, mode: str) -> dict | None:
    return None

# --- Main match analysis entrypoint ---
def format_match_embed(player: dict, match: dict, stats_block: dict, player_name: str = "Player") -> dict:
    is_turbo = match.get("gameMode") == 23
    mode = "TURBO" if is_turbo else "NON_TURBO"
    game_mode_id = match.get("gameMode")

    # ✅ Clean and safe game mode label handling
    raw_label = match.get("gameModeName")
    raw_mode = raw_label if raw_label and not raw_label.upper().startswith("MODE_") else ""
    if raw_mode:
        game_mode_name = GAME_MODE_NAMES.get(game_mode_id) or raw_mode.replace("_", " ").title()
    else:
        game_mode_name = GAME_MODE_NAMES.get(game_mode_id) or "Unknown Mode"

    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    stats = extract_player_stats(player, stats_block, team_kills, mode)
    stats["statsBlock"] = stats_block  # ✅ Ensure imp gets passed to engine_turbo

    engine = analyze_turbo if is_turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    tags = result.get("feedback_tags", {})
    is_victory = player.get("isVictory", False)
    advice = generate_advice(tags, stats, mode=mode)

    score = result.get("score", 0.0)
    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))
    title = title[:1].lower() + title[1:]  # lowercased first letter

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": score,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": match.get("durationSeconds", 0),
        "isVictory": is_victory,
        "positives": advice.get("positives", []),
        "negatives": advice.get("negatives", []),
        "flags": advice.get("flags", []),
        "tips": advice.get("tips", []),
        "matchId": match.get("id")
    }

# --- Embed formatting for Discord output ---
def build_discord_embed(result: dict) -> dict:
    from datetime import datetime, timezone

    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    title = f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title')} {kda} as {hero} — {victory}"

    duration = result.get("duration", 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    fields = [
        {
            "name": "🧮 Impact",
            "value": f"{result.get('score', 0.0):.2f} (typical in‑game: −10 to +10, high‑end ~+20–30)",
            "inline": True
        },
        {
            "name": "🧭 Role",
            "value": result.get("role", "unknown").capitalize(),
            "inline": True
        },
        {
            "name": "⚙️ Mode",
            "value": result.get("gameModeName", "Unknown Mode"),
            "inline": True
        },
        {
            "name": "⏱️ Duration",
            "value": duration_str,
            "inline": True
        },
    ]

    if result.get("positives"):
        fields.append({
            "name": "🎯 What went well",
            "value": "\n".join(f"• {line}" for line in result["positives"]),
            "inline": False
        })

    if result.get("negatives"):
        fields.append({
            "name": "🧱 What to work on",
            "value": "\n".join(f"• {line}" for line in result["negatives"]),
            "inline": False
        })

    if result.get("flags"):
        fields.append({
            "name": "📌 Flagged behavior",
            "value": "\n".join(f"• {line}" for line in result["flags"]),
            "inline": False
        })

    if result.get("tips"):
        fields.append({
            "name": "🗺️ Tips",
            "value": "\n".join(f"• {line}" for line in result["tips"]),
            "inline": False
        })

    return {
        "title": title,
        "description": "",
        "fields": fields,
        "footer": {
            "text": f"Match ID: {result['matchId']} • {now.strftime('%b %d at %-I:%M %p')}"
        },
        "timestamp": timestamp
    }
