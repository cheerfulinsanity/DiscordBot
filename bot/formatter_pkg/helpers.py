# bot/formatter_pkg/helpers.py
from __future__ import annotations
import hashlib
import random
from typing import Any, Dict, Tuple

# --- Game mode ID to label mapping (must match existing behavior) ---
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
    25: "Ranked Random Draft",
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

def normalize_hero_name(raw_name: str) -> str:
    if not raw_name:
        return "unknown"
    if raw_name.startswith("npc_dota_hero_"):
        return raw_name.replace("npc_dota_hero_", "").lower()
    return raw_name.lower()

def resolve_game_mode_name(game_mode_field: Any, raw_label: str) -> str:
    raw_up = (raw_label or "").upper()
    if isinstance(game_mode_field, str) and game_mode_field:
        return (
            RAW_MODE_LABELS.get(game_mode_field.upper())
            or RAW_MODE_LABELS.get(raw_up)
            or game_mode_field.replace("_", " ").title()
            or "Unknown"
        )
    # numeric ID path
    return (
        RAW_MODE_LABELS.get(raw_up)
        or GAME_MODE_NAMES.get(game_mode_field)
        or (raw_up.replace("_", " ").title() if raw_up else None)
        or "Unknown"
    )

def is_turbo(game_mode_field: Any, raw_label: str) -> bool:
    raw_up = (raw_label or "").upper()
    return (
        game_mode_field in (20, 23, "TURBO")
        or RAW_MODE_LABELS.get(raw_up) == "Turbo"
        or raw_up == "MODE_TURBO"
    )

def seconds_to_mmss(duration: int) -> str:
    duration = int(duration or 0)
    return f"{duration // 60}:{duration % 60:02d}"

def inject_defaults(stats: Dict[str, Any]) -> Dict[str, Any]:
    # Replace None with safe defaults by expected type, matching the old file’s behavior.
    for k in list(stats.keys()):
        v = stats[k]
        if v is None:
            if k in {"lane", "roleBasic"}:
                stats[k] = ""
            elif k == "statsBlock":
                stats[k] = {}
            else:
                stats[k] = 0
    return stats

def deterministic_seed(match_id: Any, steam_id: Any) -> str:
    seed_str = f"{match_id}:{steam_id}"
    try:
        random.seed(hashlib.md5(seed_str.encode()).hexdigest())
    except Exception:
        pass
    return seed_str
