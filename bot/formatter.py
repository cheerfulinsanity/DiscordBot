import json
from pathlib import Path
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats
from datetime import datetime
import os

# --- Canonical stat sets (for reference only) ---
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
    return raw_name.replace("npc_dota_hero_", "").lower() if raw_name.startswith("npc_dota_hero_") else raw_name.lower()

def get_role(hero_name: str) -> str:
    return "unknown"  # legacy fallback no longer used

def get_baseline(hero_name: str, mode: str) -> dict | None:
    return None  # legacy fallback no longer used

# --- Main stat extraction now uses extract.py ---
# Example usage inside your match processing loop:
#
# from feedback.extract import extract_player_stats
# stats = extract_player_stats(player, stats_block, team_kills, mode)
# feedback = analyze_normal(stats, {}, role, team_kills)
# advice = generate_advice(feedback["feedback_tags"], stats, result["isVictory"])
