# bot/formatter_pkg/core.py
from __future__ import annotations
from typing import Any, Dict
import random  # seeded via helpers.deterministic_seed

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

def format_match_embed(player: Dict[str, Any], match: Dict[str, Any], stats_block: Dict[str, Any], player_name: str = "Player") -> Dict[str, Any]:
    # Resolve mode label & turbo detection
    game_mode_field = match.get("gameMode")  # may be int or "TURBO"
    raw_label = (match.get("gameModeName") or "")
    game_mode_name = resolve_game_mode_name(game_mode_field, raw_label)
    turbo = is_turbo(game_mode_field, raw_label)
    mode = "TURBO" if turbo else "NON_TURBO"

    # Team kills for KP
    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in (match.get("players") or [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    # Extract/sanitize stats
    stats = extract_player_stats(player, stats_block or {}, team_kills, mode)
    stats["durationSeconds"] = match.get("durationSeconds", 0)
    stats = inject_defaults(stats)

    # Analyze (turbo vs non-turbo kept hard-split)
    engine = analyze_turbo if turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)
    tags = result.get("feedback_tags", {}) or {}
    is_victory = bool(player.get("isVictory", False))

    # Deterministic phrasing seed: {matchId}:{steamId}
    deterministic_seed(match.get("id"), player.get("steamAccountId"))

    # Phrase selection & title
    advice = generate_advice(tags, stats, mode=mode) or {}
    score = float(result.get("score") or 0.0)
    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))
    # Lowercase first character (matches old behavior)
    if title:
        title = title[:1].lower() + title[1:]

    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": score,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": (player.get("hero", {}) or {}).get("displayName")
                or normalize_hero_name((player.get("hero", {}) or {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": match.get("durationSeconds", 0),
        "isVictory": is_victory,
        "positives": (advice.get("positives") or [])[:3],
        "negatives": (advice.get("negatives") or [])[:3],
        "flags": (advice.get("flags") or [])[:3],
        "tips": (advice.get("tips") or [])[:3],
        "matchId": match.get("id"),
    }
