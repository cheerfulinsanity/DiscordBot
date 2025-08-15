# bot/formatter.py
import json
from pathlib import Path
import hashlib
import random
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

# --- Game mode ID to label mapping ---
GAME_MODE_NAMES = {
    0: "Unknown",
    1: "All Pick",
    2: "Captains Mode",
    3: "Random Draft",
    4: "Single Draft",
    5: "All Random",
    6: "Intro",
    7: "Diretide",
    8: "Reverse Captains Mode",
    9: "Greeviling",
    10: "Tutorial",
    11: "Mid Only",
    12: "Ability Draft",
    13: "Event",
    14: "AR Deathmatch",
    15: "1v1 Mid",
    16: "Captains Draft",
    17: "Balanced Draft",
    18: "Ability All Pick",
    20: "Turbo",
    21: "Mutation",
    22: "Ranked All Pick",
    23: "Turbo",
    24: "Ranked Draft",
    25: "Ranked Random Draft"
}

# --- Raw Stratz gameModeName fallback mappings ---
RAW_MODE_LABELS = {
    "MODE_TURBO": "Turbo",
    "MODE_ALL_PICK": "All Pick",
    "ALL_PICK_RANKED": "Ranked All Pick",
    "CAPTAINS_MODE": "Captains Mode",
    "SINGLE_DRAFT": "Single Draft",
    "RANDOM_DRAFT": "Random Draft",
    "ABILITY_DRAFT": "Ability Draft",
    "CAPTAINS_DRAFT": "Captains Draft",
    # Allow raw enums without MODE_ prefix
    "TURBO": "Turbo",
    "ALL_PICK": "All Pick",
    "RANKED_ALL_PICK": "Ranked All Pick",
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
    game_mode_field = match.get("gameMode")
    raw_label = (match.get("gameModeName") or "").upper()

    if isinstance(game_mode_field, str) and game_mode_field:
        game_mode_name = (
            RAW_MODE_LABELS.get(game_mode_field.upper())
            or RAW_MODE_LABELS.get(raw_label)
            or game_mode_field.replace("_", " ").title()
            or "Unknown"
        )
    else:
        game_mode_name = (
            RAW_MODE_LABELS.get(raw_label)
            or GAME_MODE_NAMES.get(game_mode_field)
            or (raw_label.replace("_", " ").title() if raw_label else None)
            or "Unknown"
        )

    is_turbo = (
        game_mode_field in (20, 23, "TURBO")
        or RAW_MODE_LABELS.get(raw_label) == "Turbo"
        or raw_label == "MODE_TURBO"
    )
    mode = "TURBO" if is_turbo else "NON_TURBO"

    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    stats = extract_player_stats(player, stats_block, team_kills, mode)
    stats["durationSeconds"] = match.get("durationSeconds", 0)

    for k in list(stats.keys()):
        v = stats[k]
        if v is None:
            if k in {"lane", "roleBasic"}:
                stats[k] = ""
            elif k == "statsBlock":
                stats[k] = {}
            else:
                stats[k] = 0

    engine = analyze_turbo if is_turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    tags = result.get("feedback_tags", {})
    is_victory = player.get("isVictory", False)

    try:
        seed_str = f"{match.get('id')}:{player.get('steamAccountId')}"
        random.seed(hashlib.md5(seed_str.encode()).hexdigest())
    except Exception:
        pass

    advice = generate_advice(tags, stats, mode=mode)

    score = float(result.get("score") or 0.0)
    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))
    title = title[:1].lower() + title[1:]

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
        "positives": advice.get("positives", [])[:3],
        "negatives": advice.get("negatives", [])[:3],
        "flags": advice.get("flags", [])[:3],
        "tips": advice.get("tips", [])[:3],
        "matchId": match.get("id")
    }

# --- Minimal fallback embed for IMP-missing matches ---
def format_fallback_embed(player: dict, match: dict, player_name: str = "Player", private_data_blocked: bool = False) -> dict:
    game_mode_field = match.get("gameMode")
    raw_label = (match.get("gameModeName") or "").upper()

    if isinstance(game_mode_field, str) and game_mode_field:
        game_mode_name = (
            RAW_MODE_LABELS.get(game_mode_field.upper())
            or RAW_MODE_LABELS.get(raw_label)
            or game_mode_field.replace("_", " ").title()
            or "Unknown"
        )
    else:
        game_mode_name = (
            RAW_MODE_LABELS.get(raw_label)
            or GAME_MODE_NAMES.get(game_mode_field)
            or (raw_label.replace("_", " ").title() if raw_label else None)
            or "Unknown"
        )

    is_turbo = (
        game_mode_field in (20, 23, "TURBO")
        or RAW_MODE_LABELS.get(raw_label) == "Turbo"
        or raw_label == "MODE_TURBO"
    )
    mode = "TURBO" if is_turbo else "NON_TURBO"
    is_victory = player.get("isVictory", False)

    duration = match.get("durationSeconds", 0)
    basic_stats = f"Level {player.get('level', 0)}"
    if not is_turbo:
        basic_stats += f" • {player.get('goldPerMinute', 0)} GPM • {player.get('experiencePerMinute', 0)} XPM"
    else:
        basic_stats += f" • {player.get('experiencePerMinute', 0)} XPM"

    if private_data_blocked:
        emoji = "🔒"
        title = ""
        status_note = "Public Match Data not exposed — Detailed analysis unavailable."
    else:
        emoji = "⏳"
        title = "(Pending Stats)"
        status_note = "Impact score not yet processed by Stratz — detailed analysis will appear later."

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": None,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": duration,
        "isVictory": is_victory,
        "basicStats": basic_stats,
        "statusNote": status_note,
        "matchId": match.get("id")
    }

def build_fallback_embed(result: dict) -> dict:
    from datetime import datetime, timezone
    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    title = f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title')} {kda} as {hero} — {victory}".strip()

    duration = result.get("duration", 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    fields = [
        {"name": "⚙️ Mode", "value": result.get("gameModeName", "Unknown"), "inline": True},
        {"name": "⏱️ Duration", "value": duration_str, "inline": True},
        {"name": "🧭 Role", "value": result.get("role", "unknown").capitalize(), "inline": True},
        {"name": "📊 Basic Stats", "value": result.get("basicStats", ""), "inline": False},
        {"name": "⚠️ Status", "value": result.get("statusNote", ""), "inline": False},
    ]

    return {
        "title": title,
        "description": "",
        "fields": fields,
        "footer": {"text": f"Match ID: {result['matchId']} • {now.strftime('%b %d at %-I:%M %p')}"},
        "timestamp": timestamp
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
            "value": f"{result.get('score', 0.0):.2f} (typical in-game: −10 to +10, high-end ~+20–30)",
            "inline": True
        },
        {
            "name": "🧭 Role",
            "value": result.get("role", "unknown").capitalize(),
            "inline": True
        },
        {
            "name": "⚙️ Mode",
            "value": result.get("gameModeName", "Unknown"),
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
