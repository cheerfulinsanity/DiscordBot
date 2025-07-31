# bot/fetch.py

from bot.stratz import fetch_latest_match

def get_latest_new_match(steam_id: int, last_posted_id: str | None, token: str) -> dict | None:
    match = fetch_latest_match(steam_id, token)

    if str(match["match_id"]) != str(last_posted_id):
        return match

    return None
