from typing import Dict, Any
import json

DEBUG = False  # Enable for local stat printout

# --- Canonical Normal-mode stats ---
NORMAL_STATS = [
    "gpm", "xpm", "imp", "kills", "deaths", "assists",
    "campStack", "level", "killParticipation"
]

# --- Role inference (from roleBasic and lane) ---
def _get_role_category(role: str, lane: str) -> str:
    """
    Maps roleBasic + lane to 'core' or 'support' classification.
    """
    role = (role or "").lower()
    lane = (lane or "").lower()
    if role in ['softsupport', 'hardsupport']:
        return 'support'
    if lane in ['offlane', 'safelane', 'mid']:
        return 'core'
    return 'unknown'

# --- Kill participation helper ---
def _compute_kp(kills: int, assists: int, team_kills: int) -> float:
    try:
        return (kills + assists) / team_kills if team_kills > 0 else 0.0
    except Exception:
        return 0.0

# --- Phase stub for future segmentation ---
def _segment_phases(stats_block: dict) -> dict:
    return {
        "early": {},
        "mid": {},
        "late": {}
    }

# --- Main stat tag and flag logic ---
def _select_priority_feedback(role_category: str, context: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        'highlight': None,
        'lowlight': None,
        'praises': [],
        'critiques': [],
        'compound_flags': []
    }

    # Stat extracts
    imp = context.get("imp", 0)
    gpm = context.get("gpm", 0)
    xpm = context.get("xpm", 0)
    kills = context.get("kills", 0)
    assists = context.get("assists", 0)
    deaths = context.get("deaths", 0)
    level = context.get("level", 0)
    camp_stack = context.get("campStack", 0)
    kp = context.get("killParticipation", 0)
    duration = context.get("durationSeconds", 0)
    neutral_id = context.get("neutral0Id", 0)
    gold = context.get("gold", 0)
    networth = max(context.get("networth", 1), 1)  # avoid div by 0
    intentional_feeding = context.get("intentionalFeeding", False)
    lane = context.get("lane", "").lower()
    role = context.get("roleBasic", "").lower()

    # --- Highlight / Lowlight ---
    ranked_stats = {
        "gpm": gpm,
        "xpm": xpm,
        "kills": kills,
        "assists": assists,
        "imp": imp,
        "campStack": camp_stack
    }
    result["highlight"] = max(ranked_stats, key=ranked_stats.get)
    result["lowlight"] = min(ranked_stats, key=ranked_stats.get)

    # --- Praises ---
    if kills >= 10: result['praises'].append("kills")
    if assists >= 15: result['praises'].append("assists")
    if gpm >= 600: result['praises'].append("gpm")
    if xpm >= 600: result['praises'].append("xpm")
    if imp >= 1.3: result['praises'].append("imp")
    if camp_stack >= 5: result['praises'].append("campStack")

    # --- Critiques ---
    if deaths >= 10: result['critiques'].append("deaths")
    if gpm < 350: result['critiques'].append("gpm")
    if xpm < 350: result['critiques'].append("xpm")
    if kp < 0.3: result['critiques'].append("killParticipation")

    # --- Compound flags ---
    ## Role-specific utility
    if role_category == 'support' and camp_stack == 0:
        result['compound_flags'].append("no_stacking_support")

    ## Farm vs impact misalignment
    if gpm >= 600 and imp < 0.3:
        result['compound_flags'].append("farmed_did_nothing")
    elif gpm < 400 and imp >= 1.0:
        result['compound_flags'].append("impact_without_farm")

    ## Presence flags
    if kp < 0.3 and duration >= 900:
        result['compound_flags'].append("low_kp")

    ## Feed warnings
    if deaths >= 10 and imp < 0.2:
        result['compound_flags'].append("fed_no_impact")
    if deaths >= 5 and level < 10:
        result['compound_flags'].append("fed_early")

    ## Item/utility flags
    if neutral_id in [0, None]:
        result['compound_flags'].append("no_neutral_item")
    if gold / networth >= 0.15 and gold >= 1200:
        result['compound_flags'].append("hoarded_gold")

    ## Behavior violation
    if lane in ['mid', 'jungle'] and role_category == 'support':
        result['compound_flags'].append("lane_violation")
    if intentional_feeding:
        result['compound_flags'].append("intentional_feeder")

    return result

# --- Entrypoint for analysis engine ---
def analyze_player(player_stats: Dict[str, Any], _: Dict[str, Any], role: str, team_kills: int) -> Dict[str, Any]:
    """
    Normal-mode raw stat analyzer (v4.0). Ignores hero deltas.
    Returns stat tags, compound flags, and impact score for title logic.
    """
    lane = player_stats.get("lane", "")
    role_basic = player_stats.get("roleBasic", "")
    role_category = _get_role_category(role_basic, lane)

    stats = dict(player_stats)
    stats["killParticipation"] = _compute_kp(
        stats.get("kills", 0),
        stats.get("assists", 0),
        team_kills
    )
    stats["phaseStats"] = _segment_phases(player_stats.get("statsBlock", {}))

    tags = _select_priority_feedback(role_category, stats)

    if DEBUG:
        print("🧪 analyze_player debug:")
        print("  Role:", role_basic, "| Lane:", lane, "→", role_category)
        print("  Stats:", json.dumps(stats, indent=2))
        print("  Tags:", json.dumps(tags, indent=2))

    return {
        "deltas": {},  # legacy compatibility
        "score": stats.get("imp", 0.0),  # ✅ Inject actual IMP as score
        "feedback_tags": tags
    }
