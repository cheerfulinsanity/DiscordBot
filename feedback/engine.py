# feedback/engine.py

from feedback.tier import calculate_performance_score
from feedback.context import evaluate_team_context
from feedback.advice import generate_advice
from feedback.catalog import FEEDBACK_LIBRARY

def generate_feedback(player_stats, hero_baseline, roles, is_turbo=False, team_stats=None, steam_id=None):
    def pct_diff(player, avg):
        return round((player - avg) / (avg or 1), 3)

    lines = []
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

    # Get role-based advice
    advice = generate_advice(stat_deltas, player_stats, roles, is_turbo)

    # Compute performance tier
    performance = calculate_performance_score(player_stats, hero_baseline, roles, is_turbo)

    # Get team-relative context
    team_context = None
    if team_stats and steam_id:
        team_context = evaluate_team_context(steam_id, player_stats, team_stats)

    # If praise tier but no advice, inject tag line
    if performance["tier"] == "Excellent" and not advice:
        tag_pool = FEEDBACK_LIBRARY.get("tag_excellent", {}).get("lines", [[]])[0]
        if tag_pool:
            advice = [f"You {random.choice(tag_pool)}"]

    return {
        "lines": lines,
        "advice": advice if advice else [],
        "score": performance["score"],
        "tier": performance["tier"],
        "team_context": team_context
    }
