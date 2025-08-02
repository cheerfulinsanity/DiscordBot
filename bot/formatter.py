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
    return raw_name.replace("npc_dota_hero_", "").lower()

# --- Deprecated fallback functions (preserved for stability) ---
def get_role(hero_name: str) -> str:
    return "unknown"  # no longer used

def get_baseline(hero_name: str, mode: str) -> dict | None:
    return None  # legacy

# --- Main match analysis entrypoint ---
def format_match_embed(player: dict, match: dict, stats_block: dict) -> dict:
    """
    Analyze and generate match feedback fields for a single player.
    This is the v3.5 stat-tag-based formatter. Assumes engine and extract are raw-mode.
    Returns a dict suitable for use in Discord embeds or fallback plaintext.
    """
    # Determine game mode
    is_turbo = match.get("gameMode") == 23
    mode = "TURBO" if is_turbo else "NON_TURBO"

    # Extract canonical stat bundle
    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    stats = extract_player_stats(player, stats_block, team_kills, mode)

    # Route to appropriate engine
    engine = analyze_turbo if is_turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    # Tag-based phrasing
    tags = result.get("feedback_tags", {})
    is_victory = player.get("isVictory", False)
    advice = generate_advice(tags, stats, mode=mode)

    # Title and score
    score = result.get("score", 0.0)
    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))

    # Final payload (for internal use or fallback display)
    return {
        "emoji": emoji,
        "title": title,
        "score": score,
        "mode": mode,
        "role": player.get("roleBasic", "unknown"),
        "hero": normalize_hero_name(player.get("hero", {}).get("name", "")),
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
    """
    Convert internal match analysis dict into a Discord-compatible embed.
    """
    fields = []

    if result.get("positives"):
        fields.append({
            "name": "🎯 What went well",
            "value": "\n".join(f"• {line}" for line in result["positives"]),
            "inline": False
        })

    if result.get("negatives"):
        fields.append({
            "name": "🚰 What to work on",
            "value": "\n".join(f"• {line}" for line in result["negatives"]),
            "inline": False
        })

    if result.get("flags"):
        fields.append({
            "name": "💼 Flagged behavior",
            "value": "\n".join(f"• {line}" for line in result["flags"]),
            "inline": False
        })

    if result.get("tips"):
        fields.append({
            "name": "🗾 Tips",
            "value": "\n".join(f"• {line}" for line in result["tips"]),
            "inline": False
        })

    return {
        "title": f"{result['emoji']} {result['title']} {result['kda']} as {result['hero'].capitalize()} — {'Win' if result['isVictory'] else 'Loss'}",
        "fields": fields,
        "footer": {
            "text": f"Match ID: {result['matchId']}"
        }
    }
