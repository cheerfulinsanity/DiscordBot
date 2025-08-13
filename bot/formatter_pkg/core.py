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

def format_match_embed(player: dict, match: dict, stats_block: dict, player_name: str = "Player") -> Dict[str, object]:
    # Resolve game mode and turbo flag (early split per Bible)
    game_mode_name, game_mode_field = resolve_game_mode_name(match)
    raw_label_upper = (match.get("gameModeName") or "").upper()
    turbo = is_turbo(game_mode_field, raw_label_upper)
    mode = "TURBO" if turbo else "NON_TURBO"

    # Compute team kills defensively
    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in (match.get("players") or [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    # Extract + sanitize stats
    stats = extract_player_stats(player, stats_block, team_kills, mode)
    stats["durationSeconds"] = match.get("durationSeconds", 0)
    stats = inject_defaults(stats)

    # Analyze via correct engine
    engine = analyze_turbo if turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    # Deterministic phrasing (keep existing global RNG behavior)
    deterministic_seed(match.get("id"), player.get("steamAccountId"))

    advice = generate_advice(result.get("feedback_tags", {}), stats, mode=mode)

    score = float(result.get("score") or 0.0)
    is_victory = bool(player.get("isVictory", False))
    emoji, title = get_title_phrase(score, is_victory, result.get("feedback_tags", {}).get("compound_flags", []))
    title = title[:1].lower() + title[1:] if title else ""

    # Build the result payload (embed builder consumes this)
    return {
        "playerName": player_name,
        "emoji": emoji,
        "title": title,
        "score": score,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": match.get("durationSeconds", 0),
        "isVictory": is_victory,
        "positives": (advice.get("positives") or [])[:3],
        "negatives": (advice.get("negatives") or [])[:3],
        "flags": (advice.get("flags") or [])[:3],
        "tips": (advice.get("tips") or [])[:3],
        "matchId": match.get("id"),
    }
