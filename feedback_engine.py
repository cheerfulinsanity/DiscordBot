import random
from feedback_catalog import FEEDBACK_LIBRARY

def calculate_performance_score(player_stats, hero_baseline, roles, is_turbo=False):
    def get_role_weight(stat, roles):
        ROLE_WEIGHTS = {
            "kills":      {"carry": 1.2, "mid": 1.3, "offlane": 1.0, "support": 0.6},
            "deaths":     {"carry": -2.0, "mid": -2.0, "offlane": -1.8, "support": -1.0},
            "assists":    {"carry": 0.4, "mid": 0.7, "offlane": 1.0, "support": 1.5},
            "gpm":        {"carry": 1.5, "mid": 1.3, "offlane": 1.0, "support": 0.4},
            "xpm":        {"carry": 1.0, "mid": 1.2, "offlane": 1.0, "support": 0.6},
            "last_hits":  {"carry": 1.3, "mid": 1.0, "offlane": 0.7, "support": 0.3},
            "denies":     {"carry": 0.5, "mid": 0.8, "offlane": 0.6, "support": 0.1}
        }
        weights = []
        for role in roles:
            for stat_type, values in ROLE_WEIGHTS.items():
                if stat == stat_type and role in values:
                    weights.append(values[role])
        return max(weights) if weights else 0

    deltas = {}
    weights = {}
    total_score = 0.0
    count = 0

    for stat in ["kills", "deaths", "assists", "gpm", "xpm", "last_hits", "denies"]:
        if is_turbo and stat in ("gpm", "xpm"):
            continue

        player_val = player_stats.get(stat, 0)
        baseline_val = hero_baseline.get(stat, 0)
        delta = (player_val - baseline_val) / (baseline_val or 1)
        delta = max(min(delta, 3.0), -3.0)

        deltas[stat] = delta
        weight = get_role_weight(stat, roles)
        weights[stat] = weight

        if weight != 0:
            total_score += delta * weight
            count += 1

    avg_score = total_score / count if count else 0.0

    if avg_score >= 2.0:
        tier = "Excellent"
    elif avg_score >= 0.5:
        tier = "Solid"
    elif avg_score > -0.5:
        tier = "Neutral"
    else:
        tier = "Underperformed"

    return {
        "score": round(avg_score, 2),
        "tier": tier,
        "deltas": deltas,
        "weights": weights
    }

def evaluate_team_context(player_id, player_stats, team_stats):
    def net_impact(p):
        return p["kills"] + 0.5 * p["assists"] - 2 * p["deaths"]

    ranks = {
        "impact": [],
        "gpm": [],
        "xpm": []
    }

    for p in team_stats:
        impact = net_impact(p)
        ranks["impact"].append((p["account_id"], impact))
        ranks["gpm"].append((p["account_id"], p["gpm"]))
        ranks["xpm"].append((p["account_id"], p["xpm"]))

    for key in ranks:
        ranks[key].sort(key=lambda x: x[1], reverse=True)

    def get_rank(account_id, sorted_list):
        for i, (pid, _) in enumerate(sorted_list):
            if pid == account_id:
                return i + 1
        return None

    rank_gpm = get_rank(player_id, ranks["gpm"])
    rank_xpm = get_rank(player_id, ranks["xpm"])
    rank_impact = get_rank(player_id, ranks["impact"])
    total_players = len(team_stats)

    tag = "Filler"
    summary = "Performance was there, but not game-changing."

    if rank_impact == 1:
        tag = "Backpack Carrier"
        summary = "You had the highest impact on your team. Clutch."
    elif rank_gpm == 1 and rank_xpm == 1:
        tag = "Top Farmer"
        summary = "You farmed better than anyone on your team."
    elif rank_impact == total_players:
        tag = "Deadweight"
        summary = "Rough one — your stats were bottom of the team."
    elif rank_impact <= total_players // 2:
        tag = "Did Their Bit"
        summary = "Solid contribution, middle of the board."

    return {
        "tag": tag,
        "impact_rank": rank_impact,
        "gpm_rank": rank_gpm,
        "xpm_rank": rank_xpm,
        "summary_line": summary
    }

def generate_feedback(player_stats, hero_baseline, roles, is_turbo=False, team_stats=None, steam_id=None):
    def pct_diff(player, avg):
        return round((player - avg) / (avg or 1), 3)

    lines = []
    raw_advice = []

    keys = ["kills", "deaths", "assists", "last_hits", "denies", "gpm", "xpm"]
    stat_deltas = {}
    for key in keys:
        p_val = player_stats.get(key, 0)
        avg_val = hero_baseline.get(key, 0)

        if is_turbo and key in ("gpm", "xpm"):
            lines.append(f"{key.upper()}: {p_val}")
            continue

        delta = pct_diff(p_val, avg_val)
        pct = abs(int(delta * 100))
        stat_deltas[key] = delta
        lines.append(f"{key.upper()}: {p_val} → {avg_val}  ({'-' if delta < 0 else '+'}{pct}%)")

    def pull_catalog(tag, priority):
        block = FEEDBACK_LIBRARY.get(tag)
        if block:
            lineset = random.choice(block["lines"])
            for line in lineset:
                raw_advice.append((priority, line))

    if any(r in roles for r in ["carry"]):
        if stat_deltas.get("last_hits", 0) < -0.3:
            pull_catalog("carry_no_farm", 3)
        elif stat_deltas.get("gpm", 0) > 0.1 and (stat_deltas.get("kills", 0) + stat_deltas.get("assists", 0) < -0.3):
            pull_catalog("carry_afk_farmer", 3)

    if any(r in roles for r in ["mid"]):
        if (stat_deltas.get("kills", 0) + stat_deltas.get("assists", 0) < -0.4):
            pull_catalog("mid_afk", 3)

    if any(r in roles for r in ["offlane"]):
        if stat_deltas.get("deaths", 0) > 0.3 and stat_deltas.get("assists", 0) < -0.25:
            pull_catalog("offlane_feed", 3)

    if stat_deltas.get("kills", 0) < -0.3 and stat_deltas.get("assists", 0) < -0.3 and stat_deltas.get("last_hits", 0) < -0.3:
        pull_catalog("invisible_game", 3)

    for key in keys:
        if is_turbo and key in ("gpm", "xpm"):
            continue

        delta = stat_deltas.get(key, 0)
        pct = abs(int(delta * 100))
        p_val = player_stats.get(key, 0)

        if pct >= 20:
            if key == "gpm" and delta < 0:
                if "carry" in roles:
                    raw_advice.append((2, "Low GPM for a carry. Improve farming patterns, stack camps, and avoid unnecessary fights early."))
                elif "mid" in roles:
                    raw_advice.append((2, "Mid GPM below average. Use power runes and rotations more aggressively to snowball gold."))
                else:
                    raw_advice.append((1, "Your GPM was underwhelming. Look for more efficient movement and lane uptime."))

            if key == "xpm" and delta < 0:
                if "support" in roles:
                    raw_advice.append((1, "XPM was low for a support. Try soaking side lane XP when safe or leeching off jungle fights."))
                else:
                    raw_advice.append((1, "You lagged in XP gain. Improve creep efficiency and join more team fights."))

            if key == "denies" and delta < 0:
                if "mid" in roles:
                    raw_advice.append((1, "Denies were low. Control creep equilibrium and harass through deny pressure."))
                elif "offlane" in roles:
                    raw_advice.append((1, "More denies could have improved your lane. Focus on early wave control."))

            if key == "kills" and delta < 0:
                if "carry" in roles:
                    raw_advice.append((1, "Kill count was low. Join team fights at power spikes and use smoke timings."))
                elif "mid" in roles:
                    raw_advice.append((1, "Low kills from mid. Look for early pickoffs and be active after level 6."))

            if key == "assists" and delta < 0:
                if any(r in roles for r in ["support", "hard_support", "soft_support"]):
                    pull_catalog("support_invisible", 2)
                else:
                    raw_advice.append((1, "Low assists. Be more present during team fights — even non-supports should connect."))

            if key == "deaths" and delta > 0:
                if any(r in roles for r in ["support"]):
                    raw_advice.append((1, "High death count. Be mindful of vision placement and don’t overextend without backup."))
                elif "offlane" in roles:
                    raw_advice.append((1, "You died too often. Aggression is good, but sync with your 4 and don’t dive solo."))
                else:
                    raw_advice.append((1, "Too many deaths — evaluate your map awareness, escape timing, and when you commit."))

        elif pct >= 40 and delta > 0:
            if key == "assists" and any(r in roles for r in ["support", "soft_support"]):
                raw_advice.append((0, "Great assist count — shows strong presence and map activity. Keep enabling the team."))
            if key == "gpm" and "carry" in roles:
                raw_advice.append((0, "Your GPM was excellent. Next step: Use that gold lead to close games faster."))
            if key == "deaths" and delta < 0 and p_val <= 3:
                raw_advice.append((0, "Very few deaths — your positioning and awareness paid off."))

    performance = calculate_performance_score(player_stats, hero_baseline, roles, is_turbo)

    # === Tone-aware filtering ===
    tone_mood = {
        "Excellent": "praise",
        "Solid": "light",
        "Neutral": "balanced",
        "Underperformed": "critical"
    }.get(performance["tier"], "balanced")

    max_advice = {
        "praise": 1,
        "light": 1,
        "balanced": 3,
        "critical": 3
    }[tone_mood]

    filtered_advice = []
    for priority, tip in raw_advice:
        if tone_mood == "praise" and priority >= 1:
            continue
        if tone_mood == "light" and priority > 1:
            continue
        filtered_advice.append((priority, tip))

    filtered_advice.sort(key=lambda x: -x[0])
    advice = [tip for _, tip in filtered_advice[:max_advice]]

    if tone_mood == "praise" and not advice:
        praise_pool = FEEDBACK_LIBRARY.get("tag_excellent", {}).get("lines", [[]])[0]
        if praise_pool:
            advice = [f"You {random.choice(praise_pool)}"]

    team_context = None
    if team_stats and steam_id:
        team_context = evaluate_team_context(steam_id, player_stats, team_stats)

    return {
        "lines": lines,
        "advice": advice if advice else [],
        "score": performance["score"],
        "tier": performance["tier"],
        "team_context": team_context
    }
