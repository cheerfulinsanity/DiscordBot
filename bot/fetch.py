# bot/fetch.py

from bot.stratz import fetch_latest_match, fetch_full_match
from bot.throttle import throttle  # ✅ Fixed: import throttle from dedicated module

def get_latest_new_match(steam_id: int, last_posted_id: str | None, token: str) -> dict | None:
    """
    Lightweight check: use Stratz to get latest match ID and summary.
    Only fetch full match data if match is new.
    """
    throttle()
    latest = fetch_latest_match(steam_id, token)

    if not latest:
        return None

    match_id = latest["match_id"]

    if str(match_id) == str(last_posted_id):
        return None

    throttle()
    full_data = fetch_full_match(steam_id, match_id, token)
    if not full_data:
        return None

    return {
        "match_id": match_id,
        "full_data": full_data
    }
