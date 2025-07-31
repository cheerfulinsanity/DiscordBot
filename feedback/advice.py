# feedback/advice.py

import random
from typing import Dict, List
from feedback.catalog import PHRASE_BOOK, COMPOUND_FLAGS  # ⬅ Imported from catalog

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

def generate_advice(tags: Dict, deltas: Dict[str, float]) -> str:
    lines: List[str] = []

    # Highlight
    hi = tags.get("highlight")
    if hi and hi in deltas:
        hl_line = pick_line(hi, deltas[hi])
        if hl_line:
            lines.append(f"» {hl_line}")

    # Lowlight
    lo = tags.get("lowlight")
    if lo and lo != hi and lo in deltas:
        ll_line = pick_line(lo, deltas[lo])
        if ll_line:
            lines.append(f"» {ll_line}")

    # Compound flag
    for flag in tags.get("compound_flags", []):
        options = COMPOUND_FLAGS.get(flag)
        if options:
            lines.append(f"» {random.choice(options)}")
            break  # Show only one

    # Bonus praise/crit if room
    used = {hi, lo}
    remaining = sorted(
        ((k, v) for k, v in deltas.items() if k not in used),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    for stat, delta in remaining:
        line = pick_line(stat, delta)
        if line:
            lines.append(f"» {line}")
            break

    return "\n".join(lines)
