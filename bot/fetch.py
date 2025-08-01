# bot/fetch.py

from bot.stratz import fetch_latest_match, fetch_full_match

def get_latest_new_match(steam_id: int, last_posted_id: str | None, token: str) -> dict | None:
    """
    Fetch and compare most recent match for a player. If it's new, return full data.
    Otherwise, return None to skip.
    """
    try:
        latest = fetch_latest_match(steam_id, token)
        if not latest:
            print(f"⚠️ No latest match found for {steam_id}")
            return None

        match_id = latest["match_id"]
        if str(match_id) == str(last_posted_id):
            print(f"⏩ Match {match_id} already posted for {steam_id}")
            return None

        full_data = fetch_full_match(steam_id, match_id, token)
        if not full_data:
            print(f"⚠️ Failed to fetch full match data for match {match_id}")
            return None

        return {
            "match_id": match_id,
            "full_data": full_data
        }

    except Exception as e:
        print(f"❌ Error in get_latest_new_match for {steam_id}: {e}")
        return None
