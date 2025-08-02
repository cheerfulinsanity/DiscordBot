import random
from typing import Dict, List, Optional
from feedback.catalog import PHRASE_BOOK, COMPOUND_FLAGS, TIP_LINES

def stat_allowed(stat: str, mode: str) -> bool:
    """
    Check if a stat is allowed in this mode for phrasing.
    """
    stat_def = PHRASE_BOOK.get(stat)
    if not stat_def:
        return False
    allowed_modes = stat_def.get("modes", ["ALL"])
    return "ALL" in allowed_modes or mode in allowed_modes

def generate_advice(
    tags: Dict,
    context: Dict[str, float],
    ignore_stats: Optional[List[str]] = None,
    mode: str = "NON_TURBO"
) -> Dict[str, List[str]]:
    """
    Convert feedback tags into phrased feedback. Delta-free version for v3.5.
    Uses only stat tags and compound flags. One line per section max.
    """
    if ignore_stats is None:
        ignore_stats = []

    positives = []
    negatives = []
    tips = []
    flags = []
    used = set()

    hi = tags.get("highlight")
    lo = tags.get("lowlight")
    praises = tags.get("praises", [])
    critiques = tags.get("critiques", [])
    compound_flags = tags.get("compound_flags", [])

    # --- Praise: from highlight or tagged stat ---
    if isinstance(hi, str) and hi not in ignore_stats and stat_allowed(hi, mode):
        lines = PHRASE_BOOK.get(hi, {}).get("positive", [])
        if lines:
            positives.append(random.choice(lines))
            used.add(hi)

    # Fallback praise from list
    if not positives:
        for stat in praises:
            if stat not in ignore_stats or stat_allowed(stat, mode):
                lines = PHRASE_BOOK.get(stat, {}).get("positive", [])
                if lines:
                    positives.append(random.choice(lines))
                    used.add(stat)
                    break

    # --- Critique: from lowlight or tagged stat ---
    if isinstance(lo, str) and lo != hi and lo not in ignore_stats and stat_allowed(lo, mode):
        lines = PHRASE_BOOK.get(lo, {}).get("negative", [])
        if lines:
            negatives.append(random.choice(lines))
            used.add(lo)

    # Fallback critique from list
    if not negatives:
        for stat in critiques:
            if stat not in used and stat_allowed(stat, mode):
                lines = PHRASE_BOOK.get(stat, {}).get("negative", [])
                if lines:
                    negatives.append(random.choice(lines))
                    used.add(stat)
                    break

    # --- Compound flag (one max) ---
    for flag in compound_flags:
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
                break

    # --- Tip (optional, from praise/critiqued stat) ---
    for stat in list(used) + praises + critiques:
        if stat in ignore_stats:
            continue
        tip = TIP_LINES.get(stat)
        if isinstance(tip, dict):
            allowed = tip.get("modes", ["ALL"])
            if "ALL" in allowed or mode in allowed:
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
