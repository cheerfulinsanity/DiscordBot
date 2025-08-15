# bot/formatter.py
import json
from pathlib import Path
import hashlib
import random
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats
from datetime import datetime
import os

# Public surface re-exported from formatter_pkg
from bot.formatter_pkg.stats_sets import NORMAL_STATS, TURBO_STATS
from bot.formatter_pkg.mode import resolve_game_mode_name, is_turbo_mode
from bot.formatter_pkg.util import normalize_hero_name, get_role, get_baseline
from bot.formatter_pkg.embed import build_discord_embed, build_fallback_embed

__all__ = [
    # constants
    "NORMAL_STATS", "TURBO_STATS",
    # main formatters
    "format_match_embed", "format_fallback_embed",
    # embed builders
    "build_discord_embed", "build_fallback_embed",
    # utilities (deprecated kept public)
    "normalize_hero_name", "get_role", "get_baseline",
]

# --- Private: deterministic player-name cloaking to evade naive webhook filters ---
# Applies ONLY to a specific Steam32 ID and ONLY to the PlayerName segment.
# Techniques (deterministic per matchId:steamId):
#   1) Zero‑width character insertion between some letters (visually identical).
#   2) Single homoglyph swap for one ASCII letter (confusable Unicode).
#   3) Invisible spacing variants for spaces (NBSP/thin/narrow NBSP).
_STINGKING_STEAM32 = 48165461

_CONFUSABLES = {
    # lower
    "a": "а",  # Cyrillic a U+0430
    "c": "с",  # Cyrillic es U+0441
    "e": "е",  # Cyrillic ie U+0435
    "i": "і",  # Cyrillic byelorussian-ukrainian i U+0456
    "o": "о",  # Cyrillic o U+043E
    "p": "р",  # Cyrillic er U+0440
    "x": "х",  # Cyrillic ha U+0445
    "y": "у",  # Cyrillic u U+0443
    "k": "к",  # Cyrillic ka U+043A
    # upper
    "A": "А",  # U+0410
    "C": "С",  # U+0421
    "E": "Е",  # U+0415
    "I": "І",  # U+0406
    "O": "О",  # U+041E
    "P": "Р",  # U+0420
    "X": "Х",  # U+0425
    "Y": "У",  # U+0423
    "K": "К",  # U+041A
}

_ZW = ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"]  # ZWSP/ZWNJ/ZWJ/WJ/FEFF
_SPACE_VARIANTS = ["\u00A0", "\u2009", "\u202F"]  # NBSP / thin space / narrow NBSP


def _cloak_player_name(name: str, match_id, steam_id) -> str:
    """
    Deterministically cloak a specific user's name so naive "if 'Name' in title" bots fail.
    Visual appearance in Discord is unchanged.

    Seed: f"{match_id}:{steam_id}"
    """
    try:
        base = f"{match_id}:{steam_id}"
        seed_hex = hashlib.md5(base.encode()).hexdigest()
        rng = random.Random(seed_hex)
    except Exception:
        # Fallback deterministic seed from the name itself
        rng = random.Random(hashlib.md5((name or '').encode()).hexdigest())

    # 0) Guard: only apply to the configured steam id and non-empty name
    if int(steam_id or 0) != _STINGKING_STEAM32 or not isinstance(name, str) or not name:
        return name

    out = name

    # 1) Invisible spacing variants (only if spaces exist)
    if " " in out:
        parts = []
        for ch in out:
            if ch == " ":
                parts.append(rng.choice(_SPACE_VARIANTS))
            else:
                parts.append(ch)
        out = "".join(parts)

    # 2) Single homoglyph swap (at most one character)
    swap_indexes = [i for i, ch in enumerate(out) if ch in _CONFUSABLES]
    if swap_indexes:
        i = rng.choice(swap_indexes)
        out = out[:i] + _CONFUSABLES[out[i]] + out[i + 1 :]

    # 3) Zero‑width insertion after ~50% of characters
    zws = []
    for ch in out:
        zws.append(ch)
        if rng.random() < 0.5:
            zws.append(rng.choice(_ZW))
    out = "".join(zws)

    return out


# --- Main match analysis entrypoint ---
def format_match_embed(player: dict, match: dict, stats_block: dict, player_name: str = "Player") -> dict:
    game_mode_field = match.get("gameMode")
    raw_label = (match.get("gameModeName") or "").upper()

    game_mode_name = resolve_game_mode_name(game_mode_field, raw_label)
    is_turbo = is_turbo_mode(game_mode_field, raw_label)
    mode = "TURBO" if is_turbo else "NON_TURBO"

    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    stats = extract_player_stats(player, stats_block, team_kills, mode)
    stats["durationSeconds"] = match.get("durationSeconds", 0)

    # Safe-null sweep — preserve exact behavior
    for k in list(stats.keys()):
        v = stats[k]
        if v is None:
            if k in {"lane", "roleBasic"}:
                stats[k] = ""
            elif k == "statsBlock":
                stats[k] = {}
            else:
                stats[k] = 0

    engine = analyze_turbo if is_turbo else analyze_normal
    result = engine(stats, {}, player.get("roleBasic", ""), team_kills)

    tags = result.get("feedback_tags", {})
    is_victory = player.get("isVictory", False)

    # Deterministic randomness (seeded per match:player)
    try:
        seed_str = f"{match.get('id')}:{player.get('steamAccountId')}"
        random.seed(hashlib.md5(seed_str.encode()).hexdigest())
    except Exception:
        pass

    advice = generate_advice(tags, stats, mode=mode)

    score = float(result.get("score") or 0.0)
    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))
    title = title[:1].lower() + title[1:]

    # 🔒 Cloak only the PlayerName segment for the targeted Steam32
    steam_id = player.get("steamAccountId")
    match_id = match.get("id")
    safe_name = player_name if isinstance(player_name, str) else "Player"
    cloaked_name = _cloak_player_name(safe_name, match_id, steam_id)

    return {
        "playerName": cloaked_name,
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
        "positives": advice.get("positives", [])[:3],
        "negatives": advice.get("negatives", [])[:3],
        "flags": advice.get("flags", [])[:3],
        "tips": advice.get("tips", [])[:3],
        "matchId": match.get("id")
    }

# --- Minimal fallback embed for IMP-missing matches ---
def format_fallback_embed(player: dict, match: dict, player_name: str = "Player", private_data_blocked: bool = False) -> dict:
    game_mode_field = match.get("gameMode")
    raw_label = (match.get("gameModeName") or "").upper()

    game_mode_name = resolve_game_mode_name(game_mode_field, raw_label)
    is_turbo = is_turbo_mode(game_mode_field, raw_label)
    mode = "TURBO" if is_turbo else "NON_TURBO"
    is_victory = player.get("isVictory", False)

    duration = match.get("durationSeconds", 0)
    basic_stats = f"Level {player.get('level', 0)}"
    if not is_turbo:
        basic_stats += f" • {player.get('goldPerMinute', 0)} GPM • {player.get('experiencePerMinute', 0)} XPM"
    else:
        basic_stats += f" • {player.get('experiencePerMinute', 0)} XPM"

    if private_data_blocked:
        emoji = "🔒"
        title = ""
        status_note = "Public Match Data not exposed — Detailed analysis unavailable."
    else:
        emoji = "⏳"
        title = "(Pending Stats)"
        status_note = "Impact score not yet processed by Stratz — detailed analysis will appear later."

    # 🔒 Cloak only the PlayerName segment for the targeted Steam32
    steam_id = player.get("steamAccountId")
    match_id = match.get("id")
    safe_name = player_name if isinstance(player_name, str) else "Player"
    cloaked_name = _cloak_player_name(safe_name, match_id, steam_id)

    return {
        "playerName": cloaked_name,
        "emoji": emoji,
        "title": title,
        "score": None,
        "mode": mode,
        "gameModeName": game_mode_name,
        "role": player.get("roleBasic", "unknown"),
        "hero": player.get("hero", {}).get("displayName") or normalize_hero_name(player.get("hero", {}).get("name", "")),
        "kda": f"{player.get('kills', 0)}/{player.get('deaths', 0)}/{player.get('assists', 0)}",
        "duration": duration,
        "isVictory": is_victory,
        "basicStats": basic_stats,
        "statusNote": status_note,
        "matchId": match.get("id")
    }
