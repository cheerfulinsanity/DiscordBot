# Normal and Turbo stats from original formatter.py
NORMAL_STATS = [
    "kills", "deaths", "assists", "gpm", "xpm", "lastHits",
    "denies", "heroDamage", "towerDamage", "heroHealing",
]

TURBO_STATS = [
    "kills", "deaths", "assists", "xpm", "lastHits",
    "heroDamage", "towerDamage", "heroHealing",
]

def normalize_hero_name(raw_name: str) -> str:
    if not raw_name:
        return "unknown"
    if raw_name.startswith("npc_dota_hero_"):
        return raw_name.replace("npc_dota_hero_", "").lower()
    return raw_name.lower()
