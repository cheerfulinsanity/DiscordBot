# bot/formatter.py

from feedback.engine import analyze_player
from data.hero_baselines import get_hero_baseline
from data.hero_roles import get_expected_role

def format_match(player: dict, match: dict) -> str:
    steam_id = player.get("steamAccountId")
    hero_name = player.get("hero", {}).get("name", "").replace("npc_dota_hero_", "")
    kda = f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}"
    result = "🏆 Win" if player.get("isVictory") else "💀 Loss"

    # Extract inputs needed for feedback engine
    hero_short = hero_name
    team_kills = sum(p["kills"] for p in match["players"] if p["isRadiant"] == player["isRadiant"])
    roles = get_expected_role(hero_short)
    role = roles[0] if isinstance(roles, list) else roles
    baseline = get_hero_baseline(hero_short, role)

    stats = {
        'kills': player['kills'],
        'deaths': player['deaths'],
        'assists': player['assists'],
        'gpm': player['goldPerMinute'],
        'xpm': player['experiencePerMinute'],
        'imp': player.get('imp', 0),
        'campStack': sum(player.get('stats', {}).get('campStack', [])),
        'level': player.get('stats', {}).get('level', [0])[-1] if player.get('stats', {}).get('level') else 0
    }

    analysis = analyze_player(stats, baseline, role, team_kills)
    score = analysis.get("score", 0.0)
    tags = analysis.get("feedback_tags", {})

    tag_summary = " | ".join(f"{k}={v}" for k, v in tags.items() if v)

    return (
        f"🧙 {steam_id} — {hero_name}: {kda} — {result}\n"
        f"📈 Score: {score:.2f}\n"
        f"📊 Tags: {tag_summary}"
    )
