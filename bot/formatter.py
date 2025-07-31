from feedback.engine import analyze_player


def format_match(player: dict, match: dict) -> str:
    """
    Build a basic string summary for a player's match, including performance feedback tokens.
    """
    steam_id = player.get("steamAccountId")
    hero_name = player.get("hero", {}).get("name", "").replace("npc_dota_hero_", "")
    kda = f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}"
    result = "🏆 Win" if player.get("isVictory") else "💀 Loss"

    # Call feedback engine to calculate performance tags (currently placeholders)
    feedback_tokens = analyze_player(player, match)
    feedback_summary = " | ".join(feedback_tokens)

    return f"🧙 {steam_id} — {hero_name}: {kda} — {result}\n📊 {feedback_summary}"
