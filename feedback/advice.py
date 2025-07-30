# feedback/advice.py

import random
from feedback.catalog import FEEDBACK_LIBRARY

def generate_advice(stat_deltas, player_stats, roles, is_turbo):
    raw_advice = []
    keys = ["kills", "deaths", "assists", "last_hits", "denies", "gpm", "xpm"]

    def pull_catalog(tag, priority):
        block = FEEDBACK_LIBRARY.get(tag)
        if block:
            lineset = random.choice(block["lines"])
            for line in lineset:
                raw_advice.append((priority, line))

    if any(r in roles for r in ["carry"]):
        if stat_deltas.get("last_hits", 0) < -0.3:
            pull_catalog("carry_no_farm", 3)
        elif stat_deltas.get("gpm", 0) > 0.1 and (
            stat_deltas.get("kills", 0) + stat_deltas.get("assists", 0) < -0.3
        ):
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

    # Tone gating
    tone_mood = "balanced"  # fallback
    score = sum(stat_deltas.values()) / len(stat_deltas)
    if score >= 1.5:
        tone_mood = "praise"
    elif score >= 0.5:
        tone_mood = "light"
    elif score <= -0.5:
        tone_mood = "critical"

    max_advice = {"praise": 1, "light": 1, "balanced": 3, "critical": 3}[tone_mood]

    filtered = []
    for priority, tip in sorted(raw_advice, key=lambda x: -x[0]):
        if tone_mood == "praise" and priority >= 1:
            continue
        if tone_mood == "light" and priority > 1:
            continue
        filtered.append(tip)
        if len(filtered) >= max_advice:
            break

    return filtered
