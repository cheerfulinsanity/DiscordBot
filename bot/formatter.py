# bot/formatter.py

from feedback.engine import analyze_player

def format_match(player: dict, match: dict) -> str:
    """
    Build a token-level summary for a player's match, including calculated stat feedback.
    """
    steam_id = player.get("steamAccountId")
    hero_name = player.get("hero", {}).get("name", "").replace("npc_dota_hero_", "")
    kda = f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}"
    result = "🏆 Win" if player.get("isVictory") else "💀 Loss"

    # Run core feedback engine (placeholder tag generation only)
    analysis = analyze_player(player, match)
    feedback_tags = analysis.get("feedback_tags", {})
    score = analysis.get("score", 0.0)

    tag_summary = " | ".join(
        f"{k}={v}" for k, v in feedback_tags.items() if isinstance(v, (str, float, list))
    )

    return (
        f"🧙 {steam_id} — {hero_name}: {kda} — {result}\n"
        f"📈 Score: {score:.2f}\n"
        f"📊 Tags: {tag_summary}"
    )
