# bot/formatter.py

from feedback.engine import analyze_player

EMOJI_WIN = "🏆"
EMOJI_LOSS = "💀"
EMOJI_HERO = "🧙"
EMOJI_STATS = "📊"
EMOJI_FEEDBACK = "📝"

def format_match(player_name, player_data, match_data):
    hero = player_data['hero']['name'].replace("npc_dota_hero_", "")
    kda = f"{player_data['kills']}/{player_data['deaths']}/{player_data['assists'] }"
    won = player_data['isVictory']
    emoji = EMOJI_WIN if won else EMOJI_LOSS

    # Header summary line
    summary_line = f"{EMOJI_HERO} {player_name} — {hero}: {kda} — {emoji} {'Win' if won else 'Loss'}"

    # Get feedback token dict
    feedback = analyze_player(player_data, match_data)
    token_keys = list(feedback.keys())

    # Token label line (to be replaced later)
    token_line = f"{EMOJI_STATS} {' | '.join(token_keys)}"

    # Placeholder feedback section
    feedback_lines = [f"- [{token}]" for token in token_keys]
    feedback_block = f"{EMOJI_FEEDBACK} Feedback:\n" + "\n".join(feedback_lines)

    return f"{summary_line}\n{token_line}\n{feedback_block}"
