# bot/formatter/embed.py
from datetime import datetime, timezone

def build_discord_embed(result: dict) -> dict:
    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    title = f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title')} {kda} as {hero} — {victory}"

    duration = result.get("duration", 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    fields = [
        {
            "name": "🧮 Impact",
            "value": f"{result.get('score', 0.0):.2f} (typical in-game: −10 to +10, high-end ~+20–30)",
            "inline": True
        },
        {
            "name": "🧭 Role",
            "value": result.get("role", "unknown").capitalize(),
            "inline": True
        },
        {
            "name": "⚙️ Mode",
            "value": result.get("gameModeName", "Unknown"),
            "inline": True
        },
        {
            "name": "⏱️ Duration",
            "value": duration_str,
            "inline": True
        },
    ]

    if result.get("positives"):
        fields.append({
            "name": "🎯 What went well",
            "value": "\n".join(f"• {line}" for line in result["positives"]),
            "inline": False
        })

    if result.get("negatives"):
        fields.append({
            "name": "🧱 What to work on",
            "value": "\n".join(f"• {line}" for line in result["negatives"]),
            "inline": False
        })

    if result.get("flags"):
        fields.append({
            "name": "📌 Flagged behavior",
            "value": "\n".join(f"• {line}" for line in result["flags"]),
            "inline": False
        })

    if result.get("tips"):
        fields.append({
            "name": "🗺️ Tips",
            "value": "\n".join(f"• {line}" for line in result["tips"]),
            "inline": False
        })

    return {
        "title": title,
        "description": "",
        "fields": fields,
        "footer": {
            "text": f"Match ID: {result['matchId']} • {now.strftime('%b %d at %-I:%M %p')}"
        },
        "timestamp": timestamp
    }
