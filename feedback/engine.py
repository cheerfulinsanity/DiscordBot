from typing import Dict, Any
import json

LOW_DELTA_THRESHOLD = -0.25   # Underperforming by 25% or more
HIGH_DELTA_THRESHOLD = 0.25   # Overperforming by 25% or more

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
    return 'support' if role in ['softSupport', 'hardSupport'] else 'core'

def _calculate_deltas(player_stats: Dict[str, Any], baseline_stats: Dict[str, Any], ignore_stats: list[str] = []) -> Dict[str, float]:
    deltas = {}
    for key in baseline_stats:
        if key in ignore_stats:
            continue
        player_val = player_stats.get(key)
        baseline_val = baseline_stats.get(key)
        if isinstance(player_val, (int, float)) and isinstance(baseline_val, (int, float)) and baseline_val != 0:
            deltas[key] = (player_val - baseline_val) / baseline_val
    return deltas

def _compute_kp(kills: int, assists: int, team_kills: int) -> float:
    return (kills + assists) / team_kills if team_kills > 0 else 0.0

def _score_performance(deltas: Dict[str, float], role: str) -> float:
    weights = ROLE_WEIGHTS[_get_role_category(role)]
    score = 0.0
    for stat, delta in deltas.items():
        weight = weights.get(stat, 0)
        score += delta * weight
    return score

def _select_priority_feedback(deltas: Dict[str, float], role: str, context: Dict[str, Any]) -> Dict[str, Any]:
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

    for stat, delta in deltas.items():
        if delta <= LOW_DELTA_THRESHOLD:
            result['critiques'].append(stat)
        elif delta >= HIGH_DELTA_THRESHOLD:
            result['praises'].append(stat)

    # Compound logic for support stacking
    if 'campStack' in deltas and deltas['campStack'] <= -0.8 and _get_role_category(role) == 'support':
        result['compound_flags'].append('no_stacking_support')

    # Carry with low impact despite good farm
    if 'gpm' in deltas and 'imp' in deltas:
        if deltas['gpm'] < -0.3 and deltas['imp'] >= 0:
            result['compound_flags'].append('impact_without_farm')
        if deltas['gpm'] >= 0.2 and deltas['imp'] < -0.2:
            result['compound_flags'].append('farmed_did_nothing')

    # Low kill participation
    if 'killParticipation' in deltas and deltas['killParticipation'] < -0.3:
        result['compound_flags'].append('low_kp')

    # Fed and useless
    if 'deaths' in deltas and deltas['deaths'] > 0.5 and deltas.get('imp', 0) < 0:
        result['compound_flags'].append('fed_no_impact')

    return result

def analyze_player(
    player_stats: Dict[str, Any],
    baseline_stats: Dict[str, Any],
    role: str,
    team_kills: int,
    ignore_stats: list[str] = []
) -> Dict[str, Any]:
    # Compute kill participation and enrich player stats
    kills = player_stats.get("kills", 0)
    assists = player_stats.get("assists", 0)
    player_stats["killParticipation"] = _compute_kp(kills, assists, team_kills)

    # Calculate normalized performance deltas
    deltas = _calculate_deltas(player_stats, baseline_stats, ignore_stats=ignore_stats)

    # Weighted performance score
    score = _score_performance(deltas, role)

    # Tag-based analysis for advice generation
    feedback_tags = _select_priority_feedback(deltas, role, context=player_stats)

    return {
        'deltas': deltas,
        'score': score,
        'feedback_tags': feedback_tags
    }
