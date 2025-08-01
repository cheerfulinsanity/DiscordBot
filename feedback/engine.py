from typing import Dict, Any
import json

# --- Debug toggle ---
DEBUG = False  # Set to True for diagnostic logging

# --- Canonical Normal-mode stats ---
NORMAL_STATS = [
    "gpm", "xpm", "imp", "kills", "deaths", "assists",
    "campStack", "level", "killParticipation"
]

# --- Delta thresholds ---
LOW_DELTA_THRESHOLD = -0.25
HIGH_DELTA_THRESHOLD = 0.25

# --- Role weights ---
ROLE_WEIGHTS = {
    'core': {
        'gpm': 1.2,
        'xpm': 1.0,
        'imp': 1.0,
        'kills': 0.8,
        'deaths': -0.7,
        'assists': 0.4,
        'campStack': 0.2,
        'level': 0.6,
        'killParticipation': 0.7,
    },
    'support': {
        'gpm': 0.6,
        'xpm': 0.8,
        'imp': 1.2,
        'kills': 0.4,
        'deaths': -0.6,
        'assists': 1.0,
        'campStack': 1.0,
        'level': 0.5,
        'killParticipation': 0.8,
    }
}

def _get_role_category(role: str) -> str:
    role = role.lower()
    if role in ['softsupport', 'hardsupport']:
        return 'support'
    return 'core'

def _compute_kp(kills: int, assists: int, team_kills: int) -> float:
    try:
        return (kills + assists) / team_kills if team_kills > 0 else 0.0
    except Exception:
        return 0.0

def _calculate_deltas(player_stats: Dict[str, Any], baseline_stats: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, float]:
    deltas = {}
    for stat in weights:
        p_val = player_stats.get(stat)
        b_val = baseline_stats.get(stat)
        if isinstance(p_val, (int, float)) and isinstance(b_val, (int, float)) and b_val != 0:
            try:
                deltas[stat] = (p_val - b_val) / b_val
            except ZeroDivisionError:
                deltas[stat] = 0.0
    return deltas

def _score_performance(deltas: Dict[str, float], weights: Dict[str, float]) -> float:
    return sum(deltas[stat] * weights.get(stat, 0) for stat in deltas)

def _select_priority_feedback(deltas: Dict[str, float], role: str, context: Dict[str, Any]) -> Dict[str, Any]:
    role_category = _get_role_category(role)
    result = {
        'highlight': None,
        'lowlight': None,
        'critiques': [],
        'praises': [],
        'compound_flags': []
    }

    if not deltas:
        return result

    sorted_deltas = sorted(deltas.items(), key=lambda x: x[1], reverse=True)
    result['highlight'] = sorted_deltas[0][0]
    result['lowlight'] = sorted_deltas[-1][0]

    won = context.get("isVictory", False)
    kills = context.get("kills", 0)
    imp = context.get("imp", 0)

    for stat, delta in deltas.items():
        # Critiques first
        if delta <= LOW_DELTA_THRESHOLD:
            result['critiques'].append(stat)
            continue

        # Skip praising GPM/XPM on supports
        if role_category == 'support' and stat in ['gpm', 'xpm']:
            continue

        # Suppress empty kills-based praise
        if stat == 'kills' and kills <= 3:
            continue

        # Avoid praising high GPM if impact is low
        if stat == 'gpm' and imp < 0:
            continue

        # Damp praise if lost
        if not won and stat in ['gpm', 'xpm', 'kills']:
            continue

        if delta >= HIGH_DELTA_THRESHOLD:
            result['praises'].append(stat)

    # --- Compound flags ---
    if 'campStack' in deltas and deltas['campStack'] <= -0.8 and role_category == 'support':
        result['compound_flags'].append('no_stacking_support')

    if 'gpm' in deltas and 'imp' in deltas:
        if deltas['gpm'] < -0.3 and deltas['imp'] >= 0:
            result['compound_flags'].append('impact_without_farm')
        if deltas['gpm'] >= 0.2 and deltas['imp'] < -0.2:
            result['compound_flags'].append('farmed_did_nothing')

    if 'killParticipation' in deltas and deltas['killParticipation'] < -0.3:
        result['compound_flags'].append('low_kp')

    if 'deaths' in deltas and deltas['deaths'] > 0.5 and deltas.get('imp', 0) < 0:
        result['compound_flags'].append('fed_no_impact')

    return result

def analyze_player(player_stats: Dict[str, Any], baseline_stats: Dict[str, Any], role: str, team_kills: int) -> Dict[str, Any]:
    """
    Analyze a normal-mode player stat block against role baseline.
    Expects player_stats to contain only NORMAL_STATS.
    """

    role_category = _get_role_category(role)
    if role_category not in ROLE_WEIGHTS:
        raise ValueError(f"Invalid role category derived from role: {role}")

    weights = ROLE_WEIGHTS[role_category]

    stats = dict(player_stats)
    stats["killParticipation"] = _compute_kp(
        stats.get("kills", 0),
        stats.get("assists", 0),
        team_kills
    )

    deltas = _calculate_deltas(stats, baseline_stats, weights)
    score = _score_performance(deltas, weights)
    feedback_tags = _select_priority_feedback(deltas, role, context=stats)

    if DEBUG:
        print("🧪 analyze_player debug:")
        print("  Stats:", json.dumps(stats, indent=2))
        print("  Baseline:", json.dumps(baseline_stats, indent=2))
        print("  Role:", role, "→", role_category)
        print("  Deltas:", json.dumps(deltas, indent=2))
        print("  Score:", round(score, 2))
        print("  Tags:", json.dumps(feedback_tags, indent=2))

    return {
        'deltas': deltas,
        'score': score,
        'feedback_tags': feedback_tags
    }
