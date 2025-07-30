# bot/fetch.py

from bot.opendota import fetch_recent_matches, fetch_match_details

def get_latest_full_match(steam_id32, hero_id_to_name):
    recent_matches = fetch_recent_matches(steam_id32)
    if not recent_matches:
        return None

    for match in recent_matches:
        match_id = match.get("match_id")
        match_data = fetch_match_details(match_id)
        if not match_data or "players" not in match_data:
            continue

        # Find player
        player_data = None
        for p in match_data["players"]:
            if p.get("account_id") == steam_id32:
                player_data = p
                break

        if not player_data:
            print(f"⚠️ Player {steam_id32} not found in match {match_id}")
            continue

        if player_data.get("leaver_status", 0) != 0:
            print(f"⚠️ Player left early in match {match_id}")
            continue

        player_slot = player_data["player_slot"]
        is_radiant = player_slot < 128
        radiant_win = match_data.get("radiant_win")
        won = (radiant_win and is_radiant) or (not radiant_win and not is_radiant)

        hero_id = player_data["hero_id"]
        hero_name = hero_id_to_name.get(hero_id, "Unknown Hero")
        is_turbo = match_data.get("game_mode") == 23

        # Team stats (same side)
        team_stats = []
        for p in match_data["players"]:
            if (p.get("player_slot", 0) < 128) == is_radiant:
                team_stats.append({
                    "account_id": p.get("account_id", 0),
                    "kills": p.get("kills", 0),
                    "deaths": p.get("deaths", 0),
                    "assists": p.get("assists", 0),
                    "gpm": p.get("gold_per_min", 0),
                    "xpm": p.get("xp_per_min", 0)
                })

        return {
            "match_id": match_id,
            "account_id": steam_id32,
            "kills": player_data["kills"],
            "deaths": player_data["deaths"],
            "assists": player_data["assists"],
            "last_hits": player_data["last_hits"],
            "denies": player_data["denies"],
            "gpm": player_data["gold_per_min"],
            "xpm": player_data["xp_per_min"],
            "player_slot": player_slot,
            "radiant_win": radiant_win,
            "duration": match_data["duration"],
            "hero_name": hero_name,
            "won": won,
            "is_turbo": is_turbo,
            "invalid": False,
            "team_stats": team_stats
        }

    return None  # No valid matches found
