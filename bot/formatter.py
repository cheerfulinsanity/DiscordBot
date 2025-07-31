from datetime import datetime
import time

def format_match_summary(match, steam_id):
    player = next((p for p in match["players"] if p["steamAccountId"] == steam_id), None)
    if not player:
        raise ValueError(f"Player {steam_id} not found in match data.")

    hero = player["hero"]["name"].replace("npc_dota_hero_", "")
    win = "Victory" if player["isVictory"] else "Defeat"
    kda = f"{player['kills']}/{player['deaths']}/{player['assists']}"
    gpm = player["goldPerMinute"]
    xpm = player["experiencePerMinute"]
    imp = player.get("imp", 0)

    time_str = format_unix_timestamp(match["startDateTime"])
    duration = format_duration(match["durationSeconds"])
    header = f"**{hero.title()}** — {win} ({kda})\n"
    body = f"🕒 {time_str} | ⏱️ {duration}\n"
    stats = f"📈 GPM: {gpm} | XPM: {xpm} | IMP: {imp}\n"

    return header + body + stats

def format_unix_timestamp(unix_time):
    try:
        return datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M UTC')
    except:
        return "unknown time"

def format_duration(seconds):
    try:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s"
    except:
        return "unknown duration"
