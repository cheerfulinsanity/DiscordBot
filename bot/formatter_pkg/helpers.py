from __future__ import annotations
import hashlib
import random
from typing import Any, Dict

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
    0: "Unknown", 1: "All Pick", 2: "Captains Mode", 3: "Random Draft",
    4: "Single Draft", 5: "All Random", 6: "Intro", 7: "Diretide",
    8: "Reverse Captains Mode", 9: "Greeviling", 10: "Tutorial", 11: "Mid Only",
    12: "Ability Draft", 13: "Event", 14: "AR Deathmatch", 15: "1v1 Mid",
    16: "Captains Draft", 17: "Balanced Draft", 18: "Ability All Pick",
    20: "Turbo", 21: "Mutation", 22: "Ranked All Pick", 23: "Turbo",
    24: "Ranked Draft", 25: "Ranked Random Draft",
}

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

def normalize_hero_name(raw_name: str) -> str:
    if not raw_name:
        return "unknown"
    if raw_name.startswith("npc_dota_hero_"):
        return raw_name.replace("npc_dota_hero_", "").lower()
    return raw_name.lower()

def resolve_game_mode_name(match: Dict[str, Any]) -> tuple[str, Any]:
    """Return (human-readable mode name, raw game_mode_field)."""
    game_mode_field = match.get("gameMode")  # int or str
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
    return game_mode_name, game_mode_field

def is_turbo(game_mode_field: Any, raw_label_upper: str) -> bool:
    return (
        game_mode_field in (20, 23, "TURBO")
        or RAW_MODE_LABELS.get(raw_label_upper) == "Turbo"
        or raw_label_upper == "MODE_TURBO"
    )

def deterministic_seed(match_id: Any, steam_id: Any) -> None:
    """Keep global RNG behavior identical to original."""
    try:
        seed_str = f"{match_id}:{steam_id}"
        h = hashlib.md5(seed_str.encode()).hexdigest()
        random.seed(h)
    except Exception:
        pass

def inject_defaults(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Replace None with safe defaults by expected type."""
    out = dict(stats)
    for k, v in list(out.items()):
        if v is None:
            if k in {"lane", "roleBasic"}:
                out[k] = ""
            elif k == "statsBlock":
                out[k] = {}
            else:
                out[k] = 0
    return out

def seconds_to_mmss(seconds: int) -> str:
    seconds = int(seconds or 0)
    return f"{seconds // 60}:{seconds % 60:02d}"
