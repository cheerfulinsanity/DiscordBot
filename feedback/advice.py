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
    Convert feedback tags into phrased feedback. v3.5 stat-only model.
    Returns one praise, one critique, one compound flag, and one tip if available.
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

    # --- Praise ---
    candidates = [hi] + praises
    for stat in candidates:
        if not isinstance(stat, str) or stat in ignore_stats or not stat_allowed(stat, mode):
            continue
        lines = PHRASE_BOOK.get(stat, {}).get("positive", [])
        if lines:
            positives.append(random.choice(lines))
            used.add(stat)
            break

    # --- Critique ---
    candidates = [lo] + critiques
    for stat in candidates:
        if not isinstance(stat, str) or stat in ignore_stats or stat in used or not stat_allowed(stat, mode):
            continue
        lines = PHRASE_BOOK.get(stat, {}).get("negative", [])
        if lines:
            negatives.append(random.choice(lines))
            used.add(stat)
            break

    # --- Flag (one compound only) ---
    for flag in compound_flags:
        if not isinstance(flag, str):
            continue
        entry = COMPOUND_FLAGS.get(flag)
        if not isinstance(entry, dict):
            continue
        allowed_modes = entry.get("modes", ["ALL"])
        if "ALL" not in allowed_modes and mode not in allowed_modes:
            continue
        lines = entry.get("lines", [])
        if lines:
            flags.append(random.choice(lines))
            break

    # --- Tip (optional, from praise/critique stat) ---
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
        if score >= 2.0:
            return "😓", "Tried hard but lost"
        elif score >= 0.5:
            return "💀", "Gave it a shot but lost"
        elif score >= -1.0:
            return "☠️", "Was a major factor in loss"
        else:
            return "☠️", "Got wrecked hard"
