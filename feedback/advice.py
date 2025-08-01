import random
from typing import Dict, List, Optional
from feedback.catalog import PHRASE_BOOK, COMPOUND_FLAGS, TIP_LINES

def get_tier(delta: float) -> Optional[str]:
    abs_delta = abs(delta)
    if abs_delta < 0.15:
        return None
    elif abs_delta < 0.35:
        return "mild"
    elif abs_delta < 0.6:
        return "strong"
    return "extreme"

def stat_allowed(stat: str, mode: str) -> bool:
    """
    Check if a stat is allowed in this mode for phrasing.
    """
    stat_def = PHRASE_BOOK.get(stat)
    if not stat_def:
        return False
    allowed_modes = stat_def.get("modes", ["ALL"])
    return "ALL" in allowed_modes or mode in allowed_modes

def pick_line(tag: str, delta: float, mode: str) -> Optional[str]:
    """
    Pick a phrased line from the phrase book, based on delta tier.
    Formats the delta using absolute value to avoid sign confusion.
    """
    if not stat_allowed(tag, mode):
        return None
    tier = get_tier(delta)
    if not tier:
        return None
    lines = PHRASE_BOOK.get(tag, {}).get("tiers", {}).get(tier, [])
    if not lines:
        return None
    template = random.choice(lines)
    return template.format(delta=abs(delta) * 100)  # Use absolute delta here

def generate_advice(
    tags: Dict,
    deltas: Dict[str, float],
    ignore_stats: Optional[List[str]] = None,
    mode: str = "NON_TURBO"
) -> Dict[str, List[str]]:
    """
    Convert stat deltas and feedback tags into natural language feedback.
    Fully mode-aware; avoids filtered stats and restricts compound flags.
    """
    if ignore_stats is None:
        ignore_stats = []

    positives = []
    negatives = []
    tips = []
    flags = []

    # Filter deltas based on stat allowance and ignore list
    filtered_deltas = {
        stat: delta
        for stat, delta in deltas.items()
        if stat_allowed(stat, mode) and stat not in ignore_stats
    }

    hi = tags.get("highlight")
    lo = tags.get("lowlight")
    used = set()

    # Highlight
    if isinstance(hi, str) and hi in filtered_deltas:
        delta = filtered_deltas[hi]
        line = pick_line(hi, delta, mode)
        if line:
            (positives if delta > 0 else negatives).append(line)
            used.add(hi)

    # Lowlight
    if isinstance(lo, str) and lo != hi and lo in filtered_deltas:
        delta = filtered_deltas[lo]
        line = pick_line(lo, delta, mode)
        if line:
            (positives if delta > 0 else negatives).append(line)
            used.add(lo)

    # Compound flags
    for flag in tags.get("compound_flags", []):
        if not isinstance(flag, str):
            continue
        entry = COMPOUND_FLAGS.get(flag)
        if not isinstance(entry, dict):
            continue
        allowed_modes = entry.get("modes", ["ALL"])
        if "ALL" in allowed_modes or mode in allowed_modes:
            lines = entry.get("lines", [])
            if isinstance(lines, list) and lines:
                flags.append(random.choice(lines))
                break  # Only include one flag

    # Additional delta commentary (1 extra stat not used yet)
    remaining = sorted(
        ((stat, delta) for stat, delta in filtered_deltas.items() if stat not in used),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    for stat, delta in remaining:
        line = pick_line(stat, delta, mode)
        if line:
            (positives if delta > 0 else negatives).append(line)
            tip = TIP_LINES.get(stat)
            if isinstance(tip, dict):
                modes = tip.get("modes", ["ALL"])
                if "ALL" in modes or mode in modes:
                    tips.append(tip.get("text", ""))
            break

    return {
        "positives": positives,
        "negatives": negatives,
        "flags": flags,
        "tips": tips
    }

def get_title_phrase(score: float, won: bool, compound_flags: List[str]) -> (str, str):
    """
    Return (emoji, phrase) tuple for title line based on
    performance score, win/loss, and important flags.
    """
    # Priority: flags that indicate severe negative or positive behavior
    if "fed_no_impact" in compound_flags:
        return "☠️", "Fed hard and lost the game"
    if "farmed_did_nothing" in compound_flags:
        return "💀", "Farmed but made no impact"
    if "no_stacking_support" in compound_flags:
        return "🧺", "Support who forgot to stack jungle"
    if "low_kp" in compound_flags:
        return "🤷", "Low kill participation"

    # Then handle win/loss + score tiers
    if won:
        if score >= 3.5:
            return "💨", "Blew up the game"
        elif score >= 2.0:
            return "🔥", "Went off"
        elif score >= 0.5:
            return "🎯", "Went steady"
        elif score >= -0.5:
            return "🎲", "Turned up"
        elif score >= -2.0:
            return "💀", "Struggled"
        else:
            return "☠️", "Inted it all away"
    else:
        # Loss phrases can be more empathetic or harsher
        if score >= 2.0:
            return "😓", "Tried hard but lost"
        elif score >= 0.5:
            return "💀", "Gave it a shot but lost"
        elif score >= -1.0:
            return "☠️", "Was a major factor in loss"
        else:
            return "☠️", "Got wrecked hard"
