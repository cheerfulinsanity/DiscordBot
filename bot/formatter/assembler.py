import random
import hashlib
import datetime
import os

from feedback.advice import generate_advice, get_title_phrase
from feedback.engine import analyze_normal
from feedback.engine_turbo import analyze_turbo
from extract import extract_player_stats
from .mode import GAME_MODE_NAMES, RAW_MODE_LABELS
from .util import NORMAL_STATS, TURBO_STATS, normalize_hero_name
from .embed import build_discord_embed

def format_match_embed(player, match, stats_block, player_name="Player"):
    game_mode = match.get("gameMode")
    mode_name = GAME_MODE_NAMES.get(game_mode)

    if not mode_name and isinstance(game_mode, str):
        mode_name = RAW_MODE_LABELS.get(game_mode, game_mode.replace("_", " ").title())
    elif not mode_name:
        mode_name = f"Unknown Mode {game_mode}"

    is_turbo = mode_name.lower() == "turbo" or game_mode == 23

    team_kills = sum(
        p.get("kills", 0) or 0
        for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    player_stats = extract_player_stats(match, player)

    engine = analyze_turbo if is_turbo else analyze_normal
    random.seed(f"{match['id']}:{player.get('steamId', '')}")
    analysis = engine(match, player, team_kills)

    advice = generate_advice(
        analysis, 
        NORMAL_STATS if not is_turbo else TURBO_STATS, 
        mode_name
    )

    title = get_title_phrase(player_stats, match, player, is_turbo)

    embed_data = build_discord_embed(
        title=title,
        colour=0x00FF00 if match.get("radiantWin") == player.get("isRadiant") else 0xFF0000,
        fields=advice
    )

    return embed_data
