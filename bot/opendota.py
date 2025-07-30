# bot/opendota.py

import requests

BASE_URL = "https://api.opendota.com/api"

def fetch_hero_stats():
    """Returns list of hero dicts with 'id' and 'localized_name'."""
    try:
        r = requests.get(f"{BASE_URL}/heroStats")
        if r.status_code == 200:
            return r.json()
        else:
            print("⚠️ Failed to fetch hero stats:", r.text)
    except Exception as e:
        print("⚠️ Exception fetching hero stats:", str(e))
    return []

def fetch_recent_matches(steam_id32):
    """Returns list of recent match summaries."""
    try:
        r = requests.get(f"{BASE_URL}/players/{steam_id32}/recentMatches")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"⚠️ Failed to fetch recent matches for {steam_id32}")
    except Exception as e:
        print(f"⚠️ Exception fetching recent matches for {steam_id32}: {e}")
    return []

def fetch_match_details(match_id):
    """Returns full match JSON."""
    try:
        r = requests.get(f"{BASE_URL}/matches/{match_id}")
        if r.status_code == 200:
            return r.json()
        else:
            print(f"⚠️ Failed to fetch match {match_id}")
    except Exception as e:
        print(f"⚠️ Exception fetching match {match_id}: {e}")
    return None
