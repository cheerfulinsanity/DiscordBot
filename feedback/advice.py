import random
from typing import Dict, List, Optional
from feedback.catalog import PHRASE_BOOK, COMPOUND_FLAGS, TIP_LINES, TITLE_BOOK


def stat_allowed(stat: str, mode: str) -> bool:
    """
    Check if a stat is allowed in this mode for phrasing.
    """
    if not isinstance(stat, str):
        return False
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
    Convert feedback tags into phrased feedback.
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
        if not stat_allowed(stat, mode) or stat in ignore_stats:
            continue
        lines = PHRASE_BOOK.get(stat, {}).get("positive", [])
        if lines:
            positives.append(random.choice(lines))
            used.add(stat)
            break

    # --- Critique ---
    candidates = [lo] + critiques
    for stat in candidates:
        if not stat_allowed(stat, mode) or stat in ignore_stats or stat in used:
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

    # --- Tip ---
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
    Ensures score is numeric to avoid comparison errors.
    """
    try:
        score_val = float(score)
    except (ValueError, TypeError):
        score_val = 0.0

    # Priority: flags that override title
    if "fed_no_impact" in compound_flags:
        return "☠️", "fed hard and lost the game"
    if "farmed_did_nothing" in compound_flags:
        return "💀", "farmed but made no impact"
    if "no_stacking_support" in compound_flags:
        return "🧺", "support who forgot to stack jungle"
    if "low_kp" in compound_flags:
        return "🤷", "low kill participation"

    # Tier mapping
    if won:
        if score_val >= 30:
            tier, emoji = "legendary", "🧨"
        elif score_val >= 15:
            tier, emoji = "high", "💥"
        elif score_val >= 7:
            tier, emoji = "mid", "🔥"
        elif score_val >= 2:
            tier, emoji = "low", "🎯"
        elif score_val >= -5:
            tier, emoji = "very_low", "🎲"
        else:
            tier, emoji = "negative", "🎁"
        bank = TITLE_BOOK["win"].get(tier, [])
    else:
        if score_val >= 30:
            tier, emoji = "legendary", "🧨"
        elif score_val >= 15:
            tier, emoji = "high", "💪"
        elif score_val >= 7:
            tier, emoji = "mid", "😓"
        elif score_val >= 2:
            tier, emoji = "low", "☠️"
        elif score_val >= -5:
            tier, emoji = "very_low", "💀"
        else:
            tier, emoji = "negative", "🤡"
        bank = TITLE_BOOK["loss"].get(tier, [])

    phrase = random.choice(bank) if bank else "played a game"
    return emoji, phrase
