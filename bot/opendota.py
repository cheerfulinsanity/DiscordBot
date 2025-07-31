# bot/opendota.py

import requests

BASE_URL = "https://api.opendota.com/api"

def get_latest_match_id_from_opendota(steam_id32: int) -> int | None:
    """
    Return the most recent match ID from OpenDota.
    This includes Turbo, Ranked, Unranked — all game modes.
    Requires no authentication.
    """
    try:
        url = f"{BASE_URL}/players/{steam_id32}/recentMatches"
        res = requests.get(url, timeout=10)
        res.raise_for_status()

        matches = res.json()
        if not matches:
            return None

        return matches[0].get("match_id")
    except Exception as e:
        print(f"⚠️ OpenDota match ID fetch failed for {steam_id32}: {e}")
        return None
