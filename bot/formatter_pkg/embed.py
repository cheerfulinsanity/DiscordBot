# bot/formatter_pkg/embed.py
def build_fallback_embed(result: dict) -> dict:
    from datetime import datetime, timezone
    # ✅ Steam avatar support (optional, fail-safe)
    author = {"name": result.get("playerName", "Player")}
    try:
        steam_id = result.get("steamAccountId") or result.get("steamId") or result.get("steam_id")
        if steam_id is not None:
            from bot.steam_user import get_avatar_url  # local, lightweight, cached
            avatar_url = get_avatar_url(int(steam_id))
            if avatar_url:
                author["icon_url"] = avatar_url
    except Exception as _e:
        # Non-fatal: simply omit icon_url on any failure
        pass

    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    title = f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title')} {kda} as {hero} — {victory}".strip()

    duration = result.get("duration", 0)
    duration_str = f"{duration // 60}:{duration % 60:02d}"

    now = datetime.now(timezone.utc).astimezone()
    timestamp = now.isoformat()

    fields = [
        {"name": "⚙️ Mode", "value": result.get("gameModeName", "Unknown"), "inline": True},
        {"name": "⏱️ Duration", "value": duration_str, "inline": True},
        {"name": "🧭 Role", "value": result.get("role", "unknown").capitalize(), "inline": True},
        {"name": "📊 Basic Stats", "value": result.get("basicStats", ""), "inline": False},
        {"name": "⚠️ Status", "value": result.get("statusNote", ""), "inline": False},
    ]

    return {
        "title": title,
        "description": "",
        "fields": fields,
        "footer": {"text": f"Match ID: {result['matchId']} • {now.strftime('%b %d at %-I:%M %p')}"},
        "timestamp": timestamp,
        "author": author,
    }

# --- Embed formatting for Discord output ---
def build_discord_embed(result: dict) -> dict:
    from datetime import datetime, timezone
    # ✅ Steam avatar support (optional, fail-safe)
    author = {"name": result.get("playerName", "Player")}
    try:
        steam_id = result.get("steamAccountId") or result.get("steamId") or result.get("steam_id")
        if steam_id is not None:
            from bot.steam_user import get_avatar_url  # local, lightweight, cached
            avatar_url = get_avatar_url(int(steam_id))
            if avatar_url:
                author["icon_url"] = avatar_url
    except Exception as _e:
        # Non-fatal: simply omit icon_url on any failure
        pass

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
        "timestamp": timestamp,
        "author": author,
    }
