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

def stat_allowed(stat: str, mode: str) -> bool:
    # Accepts mode: "TURBO" or "NON_TURBO"
    stat_def = PHRASE_BOOK.get(stat)
    if not stat_def:
        return False
    allowed_modes = stat_def.get("modes", ["ALL"])
    return "ALL" in allowed_modes or mode in allowed_modes

def pick_line(tag: str, delta: float, mode: str) -> str | None:
    if not stat_allowed(tag, mode):
        return None
    tier = get_tier(delta)
    if not tier:
        return None
    lines = PHRASE_BOOK.get(tag, {}).get("tiers", {}).get(tier, [])
    if not lines:
        return None
    template = random.choice(lines)
    return template.format(delta=delta * 100)

def generate_advice(tags: Dict, deltas: Dict[str, float], ignore_stats: List[str] = [], mode: str = "NON_TURBO") -> Dict[str, List[str]]:
    positives = []
    negatives = []
    tips = []
    flags = []

    # Filtered deltas
    filtered_deltas = {k: v for k, v in deltas.items() if k not in ignore_stats and stat_allowed(k, mode)}

    # Highlight
    hi = tags.get("highlight")
    if hi and hi in filtered_deltas and stat_allowed(hi, mode) and hi not in ignore_stats:
        line = pick_line(hi, filtered_deltas[hi], mode)
        if line and filtered_deltas[hi] > 0:
            positives.append(line)
        elif line:
            negatives.append(line)

    # Lowlight
    lo = tags.get("lowlight")
    if lo and lo != hi and lo in filtered_deltas and stat_allowed(lo, mode) and lo not in ignore_stats:
        line = pick_line(lo, filtered_deltas[lo], mode)
        if line and filtered_deltas[lo] > 0:
            positives.append(line)
        elif line:
            negatives.append(line)

    # Compound flags (not filtered — assume upstream logic handled this)
    for flag in tags.get("compound_flags", []):
        options = COMPOUND_FLAGS.get(flag)
        if options:
            flags.append(random.choice(options))
            break  # Only one for now

    # Additional high/low performers
    used = {hi, lo}
    remaining = sorted(
        ((k, v) for k, v in filtered_deltas.items() if k not in used),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    for stat, delta in remaining:
        if stat in ignore_stats or not stat_allowed(stat, mode):
            continue
        line = pick_line(stat, delta, mode)
        if line:
            (positives if delta > 0 else negatives).append(line)
            tip = TIP_LINES.get(stat)
            if tip and ("ALL" in tip.get("modes", []) or mode in tip.get("modes", [])):
                tips.append(tip["text"])
            break

    return {
        "positives": positives,
        "negatives": negatives,
        "flags": flags,
        "tips": tips
    }
