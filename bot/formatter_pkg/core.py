# bot/formatter_pkg/core.py
from __future__ import annotations
from typing import Any, Dict
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats
from .helpers import (
    resolve_game_mode_name,
    is_turbo as _is_turbo,
    inject_defaults,
    deterministic_seed,
    normalize_hero_name,
)

def format_match_embed(player: Dict[str, Any], match: Dict[str, Any], stats_block: Dict[str, Any], player_name: str = "Player") -> Dict[str, Any]:
    # Mode + label resolution (identical behavior)
    game_mode_name = resolve_game_mode_name(match)
    turbo = _is_turbo(match)
    mode = "TURBO" if turbo else "NON_TURBO"

    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", []) if p.get("isRadiant") == player.get("isRadiant")
    )

    # Extract + sanitize stats
    stats = extract_player_stats(player, stats_block or {}, team_kills, mode)
    stats["durationSeconds"] = match.get("durationSeconds", 0)
    stats = inject_defaults(stats)

    engine = analyze_turbo if turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)
    tags = result.get("feedback_tags", {})
    is_victory = bool(player.get("isVictory"))

    # Deterministic phrasing seed
    deterministic_seed(match.get("id"), player.get("steamAccountId"))

    advice = generate_advice(tags, stats, mode=mode)
    try:
        score = float(result.get("score") or 0.0)
    except Exception:
        score = 0.0

    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))
    if title:
        title = title[:1].lower() + title[1:]

    hero_display = (player.get("hero", {}) or {}).get("displayName")
    hero_fallba_
