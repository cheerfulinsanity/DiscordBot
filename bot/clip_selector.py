# bot/clip_selector.py

from bot.stratz import fetch_timeline_data

def pick_best_clip_from_timelines(match_id: int, steam_id: int, token: str) -> dict:
    """
    Given a match and player, return the best timestamp to clip around.
    Prioritizes: teamfight involvement > assist moments > kill moments.
    """
    data = fetch_timeline_data(match_id, token)
    if not data:
        return {"timestamp": 60, "type": "default"}

    player_stats = next(
        (p for p in data.get("playerStats", []) if p.get("steamAccountId") == steam_id),
        None
    )
    if not player_stats:
        return {"timestamp": 60, "type": "default"}

    assists = player_stats.get("assistTimeline", [])
    kills = player_stats.get("killTimeline", [])
    teamfights = data.get("teamfights", [])

    # Priority 1: Largest teamfight involving this player
    for tf in sorted(teamfights, key=lambda x: (x["endTime"] - x["startTime"]), reverse=True):
        if steam_id in [d["steamAccountId"] for d in tf.get("deaths", [])]:
            return {"timestamp": tf["startTime"], "type": "teamfight"}

    # Priority 2: Assist moment (prefer slightly after first assist)
    if assists:
        return {"timestamp": assists[min(1, len(assists) - 1)], "type": "assist"}

    # Priority 3: Kill moment (first kill)
    if kills:
        return {"timestamp": kills[0], "type": "kill"}

    # Fallback: start of match
    return {"timestamp": 60, "type": "default"}
