# feedback/engine_turbo.py

from typing import Dict, Any
import json

DEBUG = False  # Set to True for logging output

TURBO_STATS = [
    "imp", "kills", "deaths", "assists",
    "campStack", "level", "killParticipation"
]

LOW_DELTA_THRESHOLD = -0.25
HIGH_DELTA_THRESHOLD = 0.25

ROLE_WEIGHTS = {
    'core': {
        'imp': 1.0,
        'kills': 0.9,
        'deaths': -0.8,
        'assists': 0.5,
        'level': 0.6,
        'killParticipation': 0.7
    },
    'support': {
        'imp': 1.2,
        'kills': 0.4,
        'deaths': -0.6,
        'assists': 1.1,
        'campStack': 1.0,
        'level': 0.5,
        'killParticipation': 0.8
    }
}

def _get_role_category(role: str) -> str:
    role = role.lower()
    return 'support' if role in ['softsupport', 'hardsupport'] else 'core'

def _compute_kp(kills: int, assists: int, team_kills: int) -> float:
    try:
        return (kills + assists) / team_kills if team_kills > 0 else 0.0
    except Exception:
        return 0.0

def _filter_and_sanitize(stats: Dict[str, Any]) -> Dict[str, float]:
    clean = {}
    for stat in TURBO_STATS:
        val = stats.get(stat, 0)
        clean[stat] = float(val) if isinstance(val, (int, float)) else 0.0
    return clean

def _calculate_deltas(player_stats: Dict[str, float], baseline_stats: Dict[str, float], weights: Dict[str, float]) -> Dict[str, float]:
    deltas = {}
    for stat in TURBO_STATS:
        p_val = player_stats.get(stat)
        b_val = baseline_stats.get(stat)
        if isinstance(p_val, (int, float)) and isinstance(b_val, (int, float)) and b_val != 0:
            try:
                deltas[stat] = (p_val - b_val) / b_val
            except ZeroDivisionError:
                deltas[stat] = 0.0
    return deltas

def _score_performance(deltas: Dict[str, float], weights: Dict[str, float], won: bool) -> float:
    base_score = sum(deltas[stat] * weights.get(stat, 0) for stat in deltas)
    return base_score + (0.2 if won else 0.0)

def _select_priority_feedback(deltas: Dict[str, float], role_category: str, context: Dict[str, float]) -> Dict[str, Any]:
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

    combined_contribution = context.get("kills", 0) + context.get("assists", 0)
    game_duration = context.get("durationSeconds", 0)
    level = context.get("level", 0)

    for stat, delta in deltas.items():
        if delta <= LOW_DELTA_THRESHOLD:
            result['critiques'].append(stat)
        elif delta >= HIGH_DELTA_THRESHOLD:
            # avoid praising carry potential if no impact
            if stat == "kills" and combined_contribution < 3:
                continue
            result['praises'].append(stat)

    # Turbo-specific compound flags
    if 'campStack' in deltas and deltas['campStack'] <= -0.8 and role_category == 'support':
        result['compound_flags'].append('no_stacking_support')

    if 'killParticipation' in deltas:
        if deltas['killParticipation'] < -0.3 and game_duration > 1200:
            result['compound_flags'].append('low_kp')

    if 'deaths' in deltas and deltas['deaths'] > 0.5 and context.get('imp', 0) < 0:
        result['compound_flags'].append('fed_no_impact')

    if context.get("deaths", 0) >= 5 and level < 10:
        result['compound_flags'].append('fed_early')

    return result

def analyze_player(player_stats: Dict[str, Any], baseline_stats: Dict[str, Any], role: str, team_kills: int) -> Dict[str, Any]:
    role_category = _get_role_category(role)
    weights = ROLE_WEIGHTS[role_category]

    stats = _filter_and_sanitize(player_stats)
    stats["killParticipation"] = _compute_kp(
        stats.get("kills", 0),
        stats.get("assists", 0),
        team_kills
    )

    deltas = _calculate_deltas(stats, baseline_stats, weights)
    score = _score_performance(deltas, weights, won=player_stats.get("won", False))
    stats["durationSeconds"] = player_stats.get("durationSeconds", 0)

    feedback_tags = _select_priority_feedback(deltas, role_category, context=stats)

    if DEBUG:
        print("🧪 TURBO DEBUG")
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
