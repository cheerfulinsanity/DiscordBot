from typing import Dict, Any
import json

DEBUG = False  # Set to True to enable debug logging

# --- Canonical Turbo-mode stats (no GPM/XPM/Gold) ---
TURBO_STATS = [
    "imp", "kills", "deaths", "assists",
    "campStack", "level", "killParticipation"
]

def _get_role_category(role: str, lane: str) -> str:
    """
    Maps roleBasic + lane to a simplified 'core' or 'support' tag.
    """
    role = (role or "").lower()
    lane = (lane or "").lower()
    if role in ["softsupport", "hardsupport"]:
        return "support"
    if lane in ["offlane", "safelane", "mid"]:
        return "core"
    return "unknown"

def _compute_kp(kills: int, assists: int, team_kills: int) -> float:
    try:
        return (kills + assists) / team_kills if team_kills > 0 else 0.0
    except Exception:
        return 0.0

def _select_priority_feedback(role_category: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns praise, critique, and compound behavior flags based on flat thresholds.
    """
    result = {
        'highlight': None,
        'lowlight': None,
        'praises': [],
        'critiques': [],
        'compound_flags': []
    }

    # Pull context values safely
    imp = context.get("imp", 0)
    kills = context.get("kills", 0)
    assists = context.get("assists", 0)
    deaths = context.get("deaths", 0)
    camp_stack = context.get("campStack", 0)
    level = context.get("level", 0)
    kp = context.get("killParticipation", 0)
    duration = context.get("durationSeconds", 0)
    lane = context.get("lane", "")
    role = context.get("roleBasic", "")
    intentional_feeding = context.get("intentionalFeeding", False)

    # --- Highlight / lowlight: more nuanced pool ---
    ranked_stats = {
        "imp": imp,
        "kills": kills,
        "assists": assists,
        "campStack": camp_stack,
        "killParticipation": kp,
        "deaths": -deaths  # invert for lowlight fairness
    }
    result["highlight"] = max(ranked_stats, key=ranked_stats.get)
    result["lowlight"] = min(ranked_stats, key=ranked_stats.get)

    # --- Praise tags ---
    if kills >= 10: result["praises"].append("kills")
    if assists >= 15: result["praises"].append("assists")
    if imp >= 1.3: result["praises"].append("imp")
    if camp_stack >= 5: result["praises"].append("campStack")
    if kp >= 0.7: result["praises"].append("killParticipation")

    # --- Critique tags ---
    if deaths >= 10: result["critiques"].append("deaths")
    if kp < 0.3: result["critiques"].append("killParticipation")

    # --- Compound flags ---
    if role_category == "support" and camp_stack == 0:
        result['compound_flags'].append("no_stacking_support")

    if kp < 0.3 and duration > 900:
        result['compound_flags'].append("low_kp")

    if deaths >= 10 and imp < 0.2:
        result['compound_flags'].append("fed_no_impact")

    if deaths >= 5 and level < 10:
        result['compound_flags'].append("fed_early")

    if lane in ['mid', 'jungle'] and role_category == 'support':
        result['compound_flags'].append("lane_violation")

    if intentional_feeding:
        result['compound_flags'].append("intentional_feeder")

    return result

def analyze_player(player_stats: Dict[str, Any], _: Dict[str, Any], role: str, team_kills: int) -> Dict[str, Any]:
    """
    Turbo-mode analyzer using raw stats only. No deltas or baselines.
    Preserves expected return fields (deltas, score, feedback_tags).
    """
    lane = player_stats.get("lane", "")
    role_basic = player_stats.get("roleBasic", "")
    role_category = _get_role_category(role_basic, lane)

    # Copy stats and compute KP
    stats = dict(player_stats)
    stats["killParticipation"] = _compute_kp(
        stats.get("kills", 0),
        stats.get("assists", 0),
        team_kills
    )
    stats["durationSeconds"] = stats.get("durationSeconds", 0)

    # ✅ Fix: inject imp from statsBlock
    stats_block = player_stats.get("statsBlock", {})
    stats["imp"] = stats_block.get("imp", 0.0)

    tags = _select_priority_feedback(role_category, stats)

    if DEBUG:
        print("🧪 TURBO analyze_player debug:")
        print("  Role:", role_basic, "| Lane:", lane, "→", role_category)
        print("  Stats:", json.dumps(stats, indent=2))
        print("  Tags:", json.dumps(tags, indent=2))

    return {
        "deltas": {},         # preserved for formatter compatibility
        "score": stats.get("imp", 0.0),  # 🔄 use imp as the score in Turbo mode
        "feedback_tags": tags
    }
