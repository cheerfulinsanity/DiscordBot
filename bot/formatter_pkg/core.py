# bot/formatter_pkg/core.py
from __future__ import annotations
from typing import Any, Dict

from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats

from .helpers import (
    resolve_game_mode_name,
    is_turbo,
    inject_defaults,
    deterministic_seed,
    normalize_hero_name,
)

def _team_kills_for_player(match: Dict[str, Any], player: Dict[str, Any]) -> int:
    # keep the original fallback logic
    return player.get("_team_kills") or sum(
        p.get("kills", 0) for p in (match.get("players") or [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

def format_match_embed(
    player: Dict[str, Any],
    match: Dict[str, Any],
    stats_block: Dict[str, Any],
    player_name: str = "Player",
) -> Dict[str, Any]:
    game_mode_name = resolve_game_mode_name(match)
    turbo = is_turbo(match)
    mode = "TURBO" if turbo else "NON_TURBO"

    team_kills = _team_kills_for_player(match, player)

    # Extract + finalize stats
    stats = extract_player_stats(player, stats_block or {}, team_kills, mode)
    stats["durationSeconds"] = match.get("durationSeconds", 0)
    stats = inject_defaults(stats)

    # Analyze via correct engine
    engine = analyze_turbo if turbo else analyze_normal
    analysis = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    # Deterministic phrasing (keep existing global RNG behavior)
    deterministic_seed(match.get("id"), player.get("steamAccountId"))

    advice = generate_advice(analysis.get("feedback_tags", {}), stats, mode=mode)

    score = float(analysis.get("score") or 0.0)
    is_victory = bool(player.get("isVictory", False))
    emoji, title = get_title_phrase(
        score,
        is_victory,
        analysis.get("feedback_tags", {}).get("compound_flags", []),
    )
    # lower-case first char to match prior behavior
    if title:
        title = title[:1].lower() + title[1:]

    hero_display = (
        (player.get("hero") or {}).get("displayName")
        or normalize_hero_name((player.get("hero") or {}).get("name", ""))
    )

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": score,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": hero_display,
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": match.get("durationSeconds", 0),
        "isVictory": is_victory,
        "positives": (advice.get("positives") or [])[:3],
        "negatives": (advice.get("negatives") or [])[:3],
        "flags": (advice.get("flags") or [])[:3],
        "tips": (advice.get("tips") or [])[:3],
        "matchId": match.get("id"),
    }
