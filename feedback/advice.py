# feedback/advice.py

import random
from typing import Dict, List

# --- PHRASE CATALOG ---
# These are example lines. Expand as needed.
PHRASE_BOOK = {
    "gpm": {
        "mild": [
            "Farm was stable (+{delta:.0f}%)",
            "Managed decent income (+{delta:.0f}%)",
        ],
        "strong": [
            "Solid gold gain. Carried lanes economically (+{delta:.0f}%)",
            "Well-timed rotations boosted farm (+{delta:.0f}%)",
        ],
        "extreme": [
            "Gold fountain. Did you buy a Midas IRL? (+{delta:.0f}%)",
            "Did they just let you free farm all game? (+{delta:.0f}%)",
        ],
    },
    "imp": {
        "mild": ["Made presence felt (+{delta:.0f}% IMP)"],
        "strong": ["Great impact across fights (+{delta:.0f}% IMP)"],
        "extreme": ["Unreal influence. Whole game revolved around you (+{delta:.0f}% IMP)"]
    },
    "deaths": {
        "mild": ["A few too many deaths (-{delta:.0f}%)"],
        "strong": ["Died way too much (-{delta:.0f}%)"],
        "extreme": ["Are you sponsored by the enemy team? (-{delta:.0f}%)"]
    },
    "campStack": {
        "mild": ["Stacked a bit (+{delta:.0f}%)"],
        "strong": ["Good support work with stacks (+{delta:.0f}%)"],
        "extreme": ["Stacking machine. Economy enabler (+{delta:.0f}%)"]
    },
    "killParticipation": {
        "mild": ["Decent presence in fights (+{delta:.0f}%)"],
        "strong": ["Involved across most fights (+{delta:.0f}%)"],
        "extreme": ["Everywhere at once. Were you controlling both teams? (+{delta:.0f}%)"]
    }
}

COMPOUND_FLAGS = {
    "farmed_did_nothing": [
        "Farming simulator complete. Impact sold separately.",
        "Gold hoarder with zero influence. The classic fake carry."
    ],
    "no_stacking_support": [
        "No stacks. No support. No help. Just vibes.",
        "'Support' who supports themselves. Bold choice."
    ],
    "low_kp": [
        "Team fought. You didn't. Where were you?",
        "Kill participation so low it’s practically alibi-worthy."
    ],
    "fed_no_impact": [
        "Died constantly, did nothing. A spectacular display of futility.",
        "High deaths, low impact. A case study in feeding."
    ],
    "impact_without_farm": [
        "Low GPM, high impact. Carried with scraps.",
        "Minimal farm, maximum influence. Support diff."
    ]
}

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
