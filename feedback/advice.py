# feedback/advice.py

import random
from typing import Dict, List
from feedback.catalog import PHRASE_BOOK, COMPOUND_FLAGS, TIP_LINES

# --- LOGIC ---

def get_tier(delta: float) -> str | None:
    abs_delta = abs(delta)
    if abs_delta < 0.15:
        return None
    elif abs_delta < 0.35:
        return "mild"
    elif abs_delta < 0.6:
        return "strong"
    return "extreme"

def pick_line(tag: str, delta: float) -> str | None:
    tier = get_tier(delta)
    if not tier:
        return None
    lines = PHRASE_BOOK.get(tag, {}).get(tier, [])
    if not lines:
        return None
    template = random.choice(lines)
    return template.format(delta=delta * 100)

def generate_advice(tags: Dict, deltas: Dict[str, float]) -> Dict[str, List[str]]:
    positives = []
    negatives = []
    tips = []
    flags = []

    # Highlight
    hi = tags.get("highlight")
    if hi and hi in deltas:
        line = pick_line(hi, deltas[hi])
        if line and deltas[hi] > 0:
            positives.append(line)
        elif line:
            negatives.append(line)

    # Lowlight
    lo = tags.get("lowlight")
    if lo and lo != hi and lo in deltas:
        line = pick_line(lo, deltas[lo])
        if line and deltas[lo] > 0:
            positives.append(line)
        elif line:
            negatives.append(line)

    # Compound flag
    for flag in tags.get("compound_flags", []):
        options = COMPOUND_FLAGS.get(flag)
        if options:
            flags.append(random.choice(options))
            break  # Only one for now

    # Additional high/low performers
    used = {hi, lo}
    remaining = sorted(
        ((k, v) for k, v in deltas.items() if k not in used),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    for stat, delta in remaining:
        line = pick_line(stat, delta)
        if line:
            (positives if delta > 0 else negatives).append(line)
            if stat in TIP_LINES:
                tips.append(TIP_LINES[stat])
            break

    return {
        "positives": positives,
        "negatives": negatives,
        "flags": flags,
        "tips": tips
    }
