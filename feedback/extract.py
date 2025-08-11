from typing import Dict

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

# Timeline arrays we always carry through to stats["statsBlock"]
TIMELINE_ARRAY_KEYS = [
    "impPerMinute",
    "goldPerMinute",
    "networthPerMinute",
    "experiencePerMinute",
    "level",
    "heroDamagePerMinute",
    "towerDamagePerMinute",
    "actionsPerMinute",
    "campStack",
    "runes",
    "wards",
    "wardDestruction",
    "courierKills"
]

def extract_player_stats(
    player: dict,
    stats_block: dict,
    team_kills: int,
    mode: str = "NON_TURBO"
) -> Dict[str, float]:
    """
    Extracts a clean stat dict for analysis engine from raw Stratz player/match payloads.
    Includes all stat keys, lane/role context, feeding flags, derived KP, and full statsBlock with all timeline arrays.
    """
    keys = NORMAL_STATS if mode == "NON_TURBO" else TURBO_STATS
    stats_block = stats_block or {}
    stats: Dict[str, float] = {}

    for key in keys:
        val = 0

        if key == "campStack":
            val = sum(stats_block.get("campStack") or [])

        elif key == "level":
            levels = stats_block.get("level") or []
            val = levels[-1] if levels else 0

        elif key == "runePickups":
            val = len(stats_block.get("runes") or [])

        elif key == "wardsPlaced":
            val = len(stats_block.get("wards") or [])

        elif key == "sentryWardsPlaced":
            val = round(len(stats_block.get("wards") or []) / 2)

        elif key == "observerWardsPlaced":
            val = round(len(stats_block.get("wards") or []) / 2)

        elif key == "wardsDestroyed":
            val = len(stats_block.get("wardDestruction") or [])

        elif key == "killParticipation":
            val = None  # set below

        elif key == "imp":
            val = player.get("imp", 0.0)  # ✅ from top-level player

        else:
            val = stats_block.get(key, player.get(key, 0)) or 0

        stats[key] = val

    # --- Derived: killParticipation ---
    if "killParticipation" in keys:
        kills = player.get("kills", 0)
        assists = player.get("assists", 0)
        stats["killParticipation"] = round((kills + assists) / team_kills, 3) if team_kills else 0.0

    # --- Context fields required by engine ---
    stats["lane"] = player.get("lane", "")
    stats["roleBasic"] = player.get("roleBasic", "")
    stats["partyId"] = player.get("partyId")
    stats["intentionalFeeding"] = player.get("intentionalFeeding", False)
    stats["neutral0Id"] = player.get("neutral0Id", 0)
    stats["networth"] = player.get("networth", 0)
    stats["gold"] = player.get("gold", 0)
    stats["goldSpent"] = player.get("goldSpent", 0)
    stats["durationSeconds"] = player.get("durationSeconds", 0)

    # --- Always carry through full timeline arrays ---
    full_stats_block = dict(stats_block)
    for t_key in TIMELINE_ARRAY_KEYS:
        if t_key not in full_stats_block:
            full_stats_block[t_key] = player.get("stats", {}).get(t_key) or []
    stats["statsBlock"] = full_stats_block

    return stats
