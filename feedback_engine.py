import random
from feedback_catalog import FEEDBACK_LIBRARY


def generate_feedback(player_stats, hero_baseline, roles):
    """
    Generate intelligent, role-aware Dota 2 feedback for a player
    :param player_stats: dict with keys 'kills', 'deaths', 'assists', 'last_hits', 'denies'
    :param hero_baseline: dict with baseline stats for that hero
    :param roles: list of role strings (e.g., ['support'], ['carry'])
    :return: dict with 'title' (burn) and 'lines' (list of 3 feedback lines)
    """

    # Calculate stat deltas
    k, d, a, lh, dn = (
        player_stats.get("kills", 0),
        player_stats.get("deaths", 0),
        player_stats.get("assists", 0),
        player_stats.get("last_hits", 0),
        player_stats.get("denies", 0),
    )
    base = hero_baseline

    # Avoid divide-by-zero errors
    def pct_diff(player, avg):
        return (player - avg) / (avg or 1)

    deltas = {
        "kills": pct_diff(k, base["kills"]),
        "deaths": pct_diff(d, base["deaths"]),
        "assists": pct_diff(a, base["assists"]),
        "last_hits": pct_diff(lh, base["last_hits"]),
        "denies": pct_diff(dn, base["denies"]),
    }

    pattern = None

    if "support" in roles:
        if deltas["kills"] > 0.5 and deltas["assists"] < -0.3:
            pattern = "support_ks"
        elif deltas["assists"] < -0.5 and deltas["kills"] < -0.3:
            pattern = "invisible_support"

    elif "carry" in roles:
        if deltas["last_hits"] < -0.4:
            pattern = "low_lh_carry"
        elif deltas["kills"] < -0.3 and deltas["deaths"] > 0.5:
            pattern = "feeder_carry"

    elif "mid" in roles:
        if deltas["kills"] > 0.3 and deltas["last_hits"] < -0.4:
            pattern = "no_farm_mid"

    elif "offlane" in roles:
        if deltas["deaths"] > 0.4 and (a + k) < (base["assists"] + base["kills"]) * 0.6:
            pattern = "offlane_feed"

    if not pattern and all(val < -0.5 for val in deltas.values()):
        pattern = "invisible_game"

    if not pattern:
        pattern = random.choice(list(FEEDBACK_LIBRARY.keys()))

    block = FEEDBACK_LIBRARY[pattern]
    burn = random.choice(block["burns"])
    lines = [random.choice(group) for group in block["lines"]]

    return {
        "title": f"\U0001F3AF {burn}",
        "lines": lines
    }
