# bot/steam.py

import os
import requests

STEAM_KEY = os.getenv("STEAM_API_KEY")

def get_replay_meta_from_steam(match_id: int) -> dict | None:
    """
    Fetch replaySalt and clusterId for a given match using Steam Web API.
    """
    if not STEAM_KEY:
        print("❌ STEAM_API_KEY not set in environment")
        return None

    url = "https://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1/"
    params = {
        "key": STEAM_KEY,
        "match_id": match_id
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        match = response.json().get("result", {})

        cluster = match.get("cluster")
        salt = match.get("replay_salt")

        if cluster is not None and salt is not None:
            return {
                "clusterId": cluster,
                "replaySalt": salt
            }
        else:
            print(f"⚠️ Missing replay data in Steam API response for match {match_id}")
            return None

    except Exception as e:
        print(f"❌ Steam API request failed: {e}")
        return None

