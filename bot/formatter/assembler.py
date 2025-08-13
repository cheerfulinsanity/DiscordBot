# bot/formatter/assembler.py
import hashlib
import random
from feedback.engine import analyze_player as analyze_normal
from feedback.engine_turbo import analyze_player as analyze_turbo
from feedback.advice import generate_advice, get_title_phrase
from feedback.extract import extract_player_stats
from .mode import resolve_mode_name, detect_is_turbo
from .util import normalize_hero_name

# --- Canonical stat sets (reference only; preserved as in original) ---
NORMAL_STATS = [
    "kills", "deaths", "assists", "imp", "level",
    "gold", "goldSpent", "gpm", "xpm",
    "heroHealing", "heroDamage", "towerDamage", "buildingDamage", "damageTaken",
    "actionsPerMinute", "killParticipation", "fightParticipationPercent",
    "stunDuration", "disableDuration",
    "runePickups", "wardsPlaced", "sentryWardsPlaced", "observerWardsPlaced", "wardsDestroyed",
    "campStack", "neutralKills", "laneCreeps", "jungleCreeps",
    "networth", "networthPerMinute", "experiencePerMinute"
]

TURBO_STATS = [
    stat for stat in NORMAL_STATS
    if stat not in {"gpm", "xpm", "gold", "goldSpent", "networth", "networthPerMinute"}
]

def format_match_embed(player: dict, match: dict, stats_block: dict, player_name: str = "Player") -> dict:
    # Preserve exact label handling and detection semantics
    game_mode_field = match.get("gameMode")  # may be int (ID) or str enum (e.g., "TURBO")
    raw_label = (match.get("gameModeName") or "").upper()

    game_mode_name = resolve_mode_name(game_mode_field, raw_label)
    is_turbo = detect_is_turbo(game_mode_field, raw_label)
    mode = "TURBO" if is_turbo else "NON_TURBO"

    team_kills = player.get("_team_kills") or sum(
        p.get("kills", 0) for p in match.get("players", [])
        if p.get("isRadiant") == player.get("isRadiant")
    )

    # Extract player stats (unchanged)
    stats = extract_player_stats(player, stats_block, team_kills, mode)

    # Ensure correct duration source from match-level field
    stats["durationSeconds"] = match.get("durationSeconds", 0)

    # Defensive: replace None with safe defaults by expected type (unchanged)
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

    # Deterministic phrasing seed — identical to original
    try:
        seed_str = f"{match.get('id')}:{player.get('steamAccountId')}"
        random.seed(hashlib.md5(seed_str.encode()).hexdigest())
    except Exception:
        pass

    advice = generate_advice(tags, stats, mode=mode)

    score = float(result.get("score") or 0.0)  # Ensure numeric
    emoji, title = get_title_phrase(score, is_victory, tags.get("compound_flags", []))
    title = title[:1].lower() + title[1:]

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
        "positives": advice.get("positives", [])[:3],
        "negatives": advice.get("negatives", [])[:3],
        "flags": advice.get("flags", [])[:3],
        "tips": advice.get("tips", [])[:3],
        "matchId": match.get("id")
    }
