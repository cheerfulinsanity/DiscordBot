import json
from pathlib import Path
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from datetime import datetime
import os

# --- Canonical stat sets ---
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

# --- Paths ---
BASELINES_NORMAL_PATH = Path(__file__).parent / "../data/hero_baselines.json"
BASELINES_TURBO_PATH = Path(__file__).parent / "../data/hero_baselines_turbo.json"
ROLES_PATH = Path(__file__).parent / "../data/hero_roles.json"

# --- Data loads ---
def _load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return {}

HERO_BASELINES_NORMAL = _load_json(BASELINES_NORMAL_PATH)
HERO_BASELINES_TURBO = _load_json(BASELINES_TURBO_PATH)
HERO_ROLES = _load_json(ROLES_PATH)

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
    return HERO_ROLES.get(normalize_hero_name(hero_name), ["unknown"])[0]

def get_baseline(hero_name: str, mode: str) -> dict | None:
    baselines = HERO_BASELINES_TURBO if mode == "TURBO" else HERO_BASELINES_NORMAL
    return baselines.get(normalize_hero_name(hero_name))

def _extract_stats(player: dict, stats_block: dict, stat_keys: list[str]) -> dict:
    stats = {}
    stats_block = stats_block or {}

    for key in stat_keys:
        val = 0

        if key == "campStack":
            val = sum(stats_block.get("campStack") or [])

        elif key == "level":
            level_list = stats_block.get("level") or []
            val = level_list[-1] if level_list else 0

        elif key == "runePickups":
            val = len(stats_block.get("runes") or [])

        elif key == "wardsPlaced":
            val = len(stats_block.get("wards") or [])

        elif key == "sentryWardsPlaced":
            val = sum(1 for w in stats_block.get("wards") or [] if w.get("isSentry"))

        elif key == "observerWardsPlaced":
            val = sum(1 for w in stats_block.get("wards") or [] if w.get("isObserver"))

        elif key == "wardsDestroyed":
            val = len(stats_block.get("wardDestruction") or [])

        elif key == "killParticipation":
            val = None  # set below

        else:
            val = stats_block.get(key, player.get(key, 0)) or 0

        stats[key] = val

    if "killParticipation" in stat_keys:
        team_kills = player.get("_team_kills")
        if team_kills and team_kills > 0:
            stats["killParticipation"] = round((player.get("kills", 0) + player.get("assists", 0)) / team_kills, 3)
        else:
            stats["killParticipation"] = 0.0

    if os.getenv("DEBUG_MODE") == "1":
        print("🧪 Extracted stats:", json.dumps(stats, indent=2))

    return stats
