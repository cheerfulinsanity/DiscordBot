# bot/fetch.py

from bot.stratz import fetch_latest_stratz_match

def get_latest_full_match(steam_id, hero_id_to_name=None):
    return fetch_latest_stratz_match(steam_id)
