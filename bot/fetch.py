# bot/fetch.py

from bot.stratz import fetch_latest_match, fetch_full_match

def get_latest_new_match(steam_id: int, last_posted_id: str | None, token: str) -> dict | None:
    """
    Lightweight check: fetch the latest match ID and compare to state.
    Returns minimal match dict only if new.
    """
    match = fetch_latest_match(steam_id, token)

    if not match:
        return None

    if str(match["match_id"]) != str(last_posted_id):
        return match

    return None


def get_full_match_data(steam_id: int, match_id: int, token: str) -> dict | None:
    """
    Full match data fetch. Use only after confirming match is new.
    Returns full player+match data block for formatting and feedback.
    """
    return fetch_full_match(steam_id, match_id, token)
