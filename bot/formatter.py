# bot/formatter.py

import json
from feedback.engine import analyze_player

def load_hero_baseline(hero_name: str, role: str) -> dict:
    with open("data/hero_baselines.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for row in data:
        if row["hero"].lower() == hero_name.lower():
            return {
                "kills": row["kills"],
                "deaths": row["deaths"],
                "assists": row["assists"],
                "gpm": row["gpm"],
                "xpm": row["xpm"],
                "imp": 0,
                "campStack": 0,
                "level": 0,
                "killParticipation": 0,
            }
    return {
        "kills": 0, "deaths": 0, "assists": 0,
        "gpm": 1, "xpm": 1, "imp": 1,
        "campStack": 1, "level": 1, "killParticipation": 1
    }

def get_expected_role(hero_name: str) -> str:
    with open("data/hero_roles.json", "r", encoding="utf-8") as f:
        roles = json.load(f)
    role_list = roles.get(hero_name, [])
    return role_list[0] if role_list else "unknown"

def format_match(player: dict, match: dict) -> str:
    steam_id = player.get("steamAccountId")
    hero_name = player.get("hero", {}).get("name", "").replace("npc_dota_hero_", "")
    kda = f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}"
    result = "🏆 Win" if player.get("isVictory") else "💀 Loss"

    # Extract inputs needed for feedback engine
    hero_short = hero_name
    team_kills = sum(p["kills"] for p in match["players"] if p["isRadiant"] == player["isRadiant"])
    role = get_expected_role(hero_short)
    baseline = load_hero_baseline(hero_short, role)

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
