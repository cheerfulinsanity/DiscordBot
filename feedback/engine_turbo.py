# feedback/engine_turbo.py

from typing import Dict, Any
import json

LOW_DELTA_THRESHOLD = -0.25
HIGH_DELTA_THRESHOLD = 0.25

TURBO_STATS = [
    "imp", "kills", "deaths", "assists",
    "campStack", "level", "killParticipation"
]

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
    return 'support' if role in ['softSupport', 'hardSupport'] else 'core'

def _calculate_deltas(player_stats: Dict[str, Any], baseline_stats: Dict[str, Any]) -> Dict[str, float]:
    return {
        k: (player_stats[k] - v) / v
        for k, v in baseline_stats.items()
        if k in ROLE_WEIGHTS[_get_role_category(player_stats.get("role", "core"))]
        and isinstance(player_stats.get(k), (int, float)) and isinstance(v, (int, float)) and v != 0
    }

def _compute_kp(kills: int, assists: int, team_kills: int) -> float:
    return (kills + assists) / team_kills if team_kills > 0 else 0.0

def _score_performance(deltas: Dict[str, float], role: str) -> float:
    weights = ROLE_WEIGHTS[_get_role_category(role)]
    return sum(deltas.get(k, 0) * weights.get(k, 0) for k in deltas)

def _select_priority_feedback(deltas: Dict[str, float], role: str, context: Dict[str, Any]) -> Dict[str, Any]:
    result = {'highlight': None, 'lowlight': None, 'critiques': [], 'praises': [], 'compound_flags': []}
    if not deltas:
        return result

    sorted_deltas = sorted(deltas.items(), key=lambda x: x[1], reverse=True)
    result['highlight'] = sorted_deltas[0][0]
    result['lowlight'] = sorted_deltas[-1][0]

    for stat, delta in deltas.items():
        if delta <= LOW_DELTA_THRESHOLD:
            result['critiques'].append(stat)
        elif delta >= HIGH_DELTA_THRESHOLD:
            result['praises'].append(stat)

    if 'campStack' in deltas and deltas['campStack'] <= -0.8 and _get_role_category(role) == 'support':
        result['compound_flags'].append('no_stacking_support')

    if 'killParticipation' in deltas and deltas['killParticipation'] < -0.3:
        result['compound_flags'].append('low_kp')

    if 'deaths' in deltas and deltas['deaths'] > 0.5 and deltas.get('imp', 0) < 0:
        result['compound_flags'].append('fed_no_impact')

    return result

def analyze_player(player_stats: Dict[str, Any], baseline_stats: Dict[str, Any], role: str, team_kills: int) -> Dict[str, Any]:
    # Compute KP first
    player_stats["killParticipation"] = _compute_kp(
        player_stats.get("kills", 0),
        player_stats.get("assists", 0),
        team_kills
    )

    # Strip illegal stats
    filtered_stats = {k: v for k, v in player_stats.items() if k in TURBO_STATS}
    filtered_stats["role"] = role  # needed by _get_role_category during delta calculation

    deltas = _calculate_deltas(filtered_stats, baseline_stats)
    score = _score_performance(deltas, role)
    tags = _select_priority_feedback(deltas, role, context=filtered_stats)

    return {
        'deltas': deltas,
        'score': score,
        'feedback_tags': tags
    }
