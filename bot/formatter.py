# bot/formatter.py

import time
import random
from feedback.engine import generate_feedback
from feedback.catalog import FEEDBACK_LIBRARY

def format_message(name, match, hero_roles, hero_baseline_map):
    k, d, a = match['kills'], match['deaths'], match['assists']
    duration = time.strftime("%Mm%Ss", time.gmtime(match['duration']))
    match_url = f"https://www.opendota.com/matches/{match['match_id']}"
    is_turbo = match.get("is_turbo", False)

    match_type_label = f"{'Victory!' if match['won'] else 'Defeat.'}"
    if is_turbo:
        match_type_label += " (Turbo Match)"

    hero_name = match['hero_name']
    baseline = hero_baseline_map.get(hero_name)
    roles = hero_roles.get(hero_name, [])

    feedback = None
    tag_line = "did something."
    team_role_line = ""
    summary_line = ""

    above = []
    below = []
    raw = []

    if baseline and roles:
        player_stats = {
            "kills": k,
            "deaths": d,
            "assists": a,
            "last_hits": match.get("last_hits", 0),
            "denies": match.get("denies", 0),
            "gpm": match.get("gpm", 0),
            "xpm": match.get("xpm", 0)
        }

        feedback = generate_feedback(
            player_stats,
            baseline,
            roles,
            is_turbo=is_turbo,
            team_stats=match.get("team_stats"),
            steam_id=match.get("account_id")
        )

        ctx = feedback.get("team_context")
        if ctx:
            team_role_line = (
                f"🛡️ Team Role: {ctx['tag']} | Impact Rank: {ctx['impact_rank']} "
                f"| GPM Rank: {ctx['gpm_rank']} | XPM Rank: {ctx['xpm_rank']}"
            )
            summary_line = f"💬 *{ctx['summary_line']}*"
        else:
            tier = feedback.get("tier", "").lower()
            tier_tag = {
                "excellent": "smashed",
                "solid": "did_work",
                "neutral": "even_game",
                "underperformed": "fed"
            }.get(tier)
            if tier_tag:
                flavor_block = FEEDBACK_LIBRARY.get(f"tag_{tier_tag}")
                if flavor_block:
                    tag_line = random.choice(flavor_block["lines"][0])

        for line in feedback.get("lines", []):
            if "→" not in line:
                raw.append(line)
                continue
            pct = line.split("(")[-1].strip(")%")
            try:
                delta = int(pct.replace("+", "").replace("-", ""))
                if "-" in line and delta >= 5:
                    below.append(line)
                elif "+" in line and delta >= 5:
                    above.append(line)
            except:
                continue

    msg = f"{'🟢' if match['won'] else '🔴'} **{name}** went `{k}/{d}/{a}`"
    if team_role_line:
        msg += f" — {team_role_line}"
    else:
        msg += f" — {tag_line}"
    msg += f"\n**{match_type_label}** | ⏱ {duration}\n🔗 {match_url}"

    if baseline and roles:
        msg += f"\n\n🎯 **Stats vs Avg ({hero_name})**"
        if below:
            msg += "\n**📉 Below Average:**"
            for line in below:
                msg += f"\n- {line}"
        if above:
            msg += "\n**📈 Above Average:**"
            for line in above:
                msg += f"\n- {line}"
        if raw:
            msg += "\n**🔢 Raw Stats (Turbo Mode):**"
            for line in raw:
                msg += f"\n- {line}"
        if "advice" in feedback and feedback["advice"]:
            msg += "\n\n🛠️ **Advice**"
            for tip in feedback["advice"]:
                msg += f"\n- {tip}"

    if summary_line:
        msg += f"\n\n{summary_line}"

    return msg.strip()
