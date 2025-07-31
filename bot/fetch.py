# bot/fetch.py

from bot.opendota import get_latest_match_id_from_opendota
from bot.stratz import fetch_full_match

def get_latest_new_match(steam_id: int, last_posted_id: str | None, token: str) -> dict | None:
    """
    Lightweight check: use OpenDota to get latest match ID.
    Only fetch full match data from Stratz if new.
    """
    latest_id = get_latest_match_id_from_opendota(steam_id)

    if not latest_id:
        return None

    if str(latest_id) == str(last_posted_id):
        return None

    full_data = fetch_full_match(steam_id, latest_id, token)
    if not full_data:
        return None

    return {
        "match_id": latest_id,
        "full_data": full_data
    }
