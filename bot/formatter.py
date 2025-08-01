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

TURBO_STATS = [s for s in NORMAL_STATS if s not in ["gpm", "xpm", "gold", "goldSpent", "networth", "networthPerMinute"]]

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

        elif key == "runePickups":
            runes = stats_block.get("runes") or []
            stats["runePickups"] = len(runes)

        elif key == "wardsPlaced":
            wards = stats_block.get("wards") or []
            stats["wardsPlaced"] = len(wards)

        elif key == "sentryWardsPlaced":
            sentries = [w for w in stats_block.get("wards") or [] if w.get("isSentry")]
            stats["sentryWardsPlaced"] = len(sentries)

        elif key == "observerWardsPlaced":
            observers = [w for w in stats_block.get("wards") or [] if w.get("isObserver")]
            stats["observerWardsPlaced"] = len(observers)

        elif key == "wardsDestroyed":
            destroyed = stats_block.get("wardDestruction") or []
            stats["wardsDestroyed"] = len(destroyed)

        elif key == "killParticipation":
            stats["killParticipation"] = None  # Placeholder, calculated later

        else:
            stats[key] = stats_block.get(key)
            if stats[key] is None:
                stats[key] = player.get(key, 0)
            if stats[key] is None:
                stats[key] = 0

    if os.getenv("DEBUG_MODE") == "1":
        print("🧪 Extracted stats:", json.dumps(stats, indent=2))

    return stats
