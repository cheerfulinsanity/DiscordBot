# extract.py
# Schema-aligned extraction from Stratz GraphQL match payload
# Expanded to include all timeline and event data for richer future analysis

def extract_match_data(match_json):
    """
    Extracts structured match data from a Stratz GraphQL match payload.

    Returns:
        dict: {
            match_id, duration, game_mode, is_turbo, start_time,
            players: [ { ... expanded player stats ... } ]
        }
    """
    match = match_json.get("data", {}).get("match", {})
    if not match:
        return {}

    match_id = match.get("id")
    duration = match.get("durationSeconds")
    game_mode = match.get("gameMode", "")
    start_time = match.get("startDateTime")
    is_turbo = (game_mode.upper() == "TURBO")

    players_data = []
    for p in match.get("players", []):
        stats = p.get("stats", {}) or {}

        player_entry = {
            # --- Basic Info ---
            "steam_id": p.get("steamAccountId"),
            "is_radiant": p.get("isRadiant"),
            "is_victory": p.get("isVictory"),
            "lane": p.get("lane"),
            "role": p.get("roleBasic"),
            "party_id": p.get("partyId"),
            "intentional_feeding": p.get("intentionalFeeding"),

            # --- Totals ---
            "kills": p.get("kills", 0),
            "deaths": p.get("deaths", 0),
            "assists": p.get("assists", 0),
            "imp": p.get("imp", 0),
            "gold": p.get("gold", 0),
            "gold_spent": p.get("goldSpent", 0),
            "networth": p.get("networth", 0),
            "gpm": p.get("goldPerMinute", 0),
            "xpm": p.get("experiencePerMinute", 0),
            "level": p.get("level", 0),
            "hero_damage": p.get("heroDamage", 0),
            "tower_damage": p.get("towerDamage", 0),
            "hero_healing": p.get("heroHealing", 0),

            # --- Timelines ---
            "timelines": {
                "campStack": stats.get("campStack", []),
                "level": stats.get("level", []),
                "networthPerMinute": stats.get("networthPerMinute", []),
                "goldPerMinute": stats.get("goldPerMinute", []),
                "experiencePerMinute": stats.get("experiencePerMinute", []),
                "actionsPerMinute": stats.get("actionsPerMinute", []),
                "heroDamagePerMinute": stats.get("heroDamagePerMinute", []),
                "towerDamagePerMinute": stats.get("towerDamagePerMinute", []),
                "impPerMinute": stats.get("impPerMinute", []),
            },

            # --- Events ---
            "events": {
                "wards": stats.get("wards", []),
                "wardDestruction": stats.get("wardDestruction", []),
                "runes": stats.get("runes", []),
            }
        }

        players_data.append(player_entry)

    return {
        "match_id": match_id,
        "duration": duration,
        "game_mode": game_mode,
        "is_turbo": is_turbo,
        "start_time": start_time,
        "players": players_data
    }


def extract_for_engine(match_json):
    """
    Extracts match data in a format that is compatible with both engine.py and engine_turbo.py.

    Hard-splits processing based on Turbo/Normal mode.
    """
    match_data = extract_match_data(match_json)
    if not match_data:
        return {}

    if match_data["is_turbo"]:
        # Turbo mode – skip certain economy stats if engines don't use them
        return {
            **match_data,
            "mode": "turbo"
        }
    else:
        # Normal mode – keep full set
        return {
            **match_data,
            "mode": "normal"
        }
