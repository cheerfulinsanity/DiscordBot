# feedback/advice.py
import random
from typing import Dict, List, Optional, Any
from feedback.catalog import PHRASE_BOOK, COMPOUND_FLAGS, TIP_LINES, TITLE_BOOK

# -------------------------
# Band-aware advice selector
# -------------------------

# Band keys per polarity
POS_BANDS = ["light", "moderate", "high", "extreme"]
NEG_BANDS = ["light", "moderate", "severe", "critical"]

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


def _safe_num(x: Any, default: float | None = None) -> Optional[float]:
    try:
        if x is None:
            return default
        if isinstance(x, bool):
            return float(x)
        return float(x)
    except (TypeError, ValueError):
        return default


def _flatten_bands(lines_def: Any) -> List[str]:
    """
    Accept either a flat list or a dict-of-bands and return a flat list of lines.
    """
    if isinstance(lines_def, list):
        return [s for s in lines_def if isinstance(s, str) and s.strip()]
    if isinstance(lines_def, dict):
        out: List[str] = []
        for v in lines_def.values():
            if isinstance(v, list):
                out.extend([s for s in v if isinstance(s, str) and s.strip()])
        return out
    return []


def _band_for_stat(stat: str, value: Optional[float], polarity: str) -> str:
    """
    Map a numeric value to a band for the given stat and polarity.
    If value is None, choose a neutral band ('moderate').
    Thresholds are intentionally conservative and stat-local.
    """
    if value is None:
        return "moderate"

    # IMP (for stat phrasing only; title bands are handled separately)
    if stat == "imp":
        if polarity == "positive":
            if value >= 15: return "extreme"
            if value >= 8:  return "high"
            if value >= 3:  return "moderate"
            return "light"
        else:
            if value <= -15: return "critical"
            if value <= -8:  return "severe"
            if value <= -3:  return "moderate"
            return "light"

    if stat == "kills":
        if polarity == "positive":
            if value >= 18: return "extreme"
            if value >= 12: return "high"
            if value >= 6:  return "moderate"
            return "light"
        else:
            if value <= 0:  return "critical"
            if value <= 2:  return "severe"
            if value <= 4:  return "moderate"
            return "light"

    if stat == "deaths":
        if polarity == "positive":
            if value <= 0:  return "extreme"
            if value <= 2:  return "high"
            if value <= 5:  return "moderate"
            return "light"
        else:
            if value >= 12: return "critical"
            if value >= 9:  return "severe"
            if value >= 6:  return "moderate"
            return "light"

    if stat == "assists":
        if polarity == "positive":
            if value >= 24: return "extreme"
            if value >= 16: return "high"
            if value >= 10: return "moderate"
            return "light"
        else:
            if value <= 1:  return "critical"
            if value <= 3:  return "severe"
            if value <= 6:  return "moderate"
            return "light"

    if stat == "level":
        if polarity == "positive":
            if value >= 26: return "extreme"
            if value >= 23: return "high"
            if value >= 18: return "moderate"
            return "light"
        else:
            if value <= 12: return "critical"
            if value <= 16: return "severe"
            if value <= 18: return "moderate"
            return "light"

    if stat == "killParticipation":
        if polarity == "positive":
            if value >= 0.80: return "extreme"
            if value >= 0.65: return "high"
            if value >= 0.50: return "moderate"
            return "light"
        else:
            if value <= 0.20: return "critical"
            if value <= 0.30: return "severe"
            if value <= 0.45: return "moderate"
            return "light"

    # Economy metrics (NON_TURBO only; gating handled by stat_allowed)
    if stat == "gpm":
        if polarity == "positive":
            if value >= 650: return "extreme"
            if value >= 550: return "high"
            if value >= 450: return "moderate"
            return "light"
        else:
            if value <= 250: return "critical"
            if value <= 320: return "severe"
            if value <= 400: return "moderate"
            return "light"

    if stat == "xpm":
        if polarity == "positive":
            if value >= 700: return "extreme"
            if value >= 600: return "high"
            if value >= 500: return "moderate"
            return "light"
        else:
            if value <= 300: return "critical"
            if value <= 380: return "severe"
            if value <= 460: return "moderate"
            return "light"

    # Vision/utility
    if stat == "campStack":
        if polarity == "positive":
            if value >= 10: return "extreme"
            if value >= 7:  return "high"
            if value >= 4:  return "moderate"
            return "light"
        else:
            if value <= 0:  return "critical"
            if value <= 1:  return "severe"
            if value <= 3:  return "moderate"
            return "light"

    return "moderate"


def _stat_value_from_context(stat: str, ctx: Dict[str, Any]) -> Optional[float]:
    if stat == "killParticipation":
        return _safe_num(ctx.get("killParticipation"))
    return _safe_num(ctx.get(stat))


def _choose_banded_line(stat: str, polarity: str, context: Dict[str, Any]) -> Optional[str]:
    entry = PHRASE_BOOK.get(stat, {})
    lines_def = entry.get(polarity, [])

    # Legacy flat list support
    if isinstance(lines_def, list):
        flat = _flatten_bands(lines_def)
        return random.choice(flat) if flat else None

    # Banded dict
    if isinstance(lines_def, dict):
        val = _stat_value_from_context(stat, context)
        band = _band_for_stat(stat, val, polarity)
        lines = lines_def.get(band) or []
        if not lines:
            flat = _flatten_bands(lines_def)
            return random.choice(flat) if flat else None
        return random.choice(lines)

    return None


def _choose_banded_tip(stat: str, context: Dict[str, Any], mode: str) -> Optional[str]:
    tip_entry = TIP_LINES.get(stat)
    if not isinstance(tip_entry, dict):
        return None
    allowed_modes = tip_entry.get("modes", ["ALL"])
    if "ALL" not in allowed_modes and mode not in allowed_modes:
        return None
    tip_text = tip_entry.get("text")
    if isinstance(tip_text, str):
        return tip_text
    if isinstance(tip_text, dict):
        val = _stat_value_from_context(stat, context)
        # Tips are constructive: map via positive polarity bands
        band = _band_for_stat(stat, val, "positive")
        lines = tip_text.get(band) or []
        if lines and isinstance(lines, list):
            return random.choice(lines)
    return None


def generate_advice(
    tags: Dict,
    context: Dict[str, float],
    ignore_stats: Optional[List[str]] = None,
    mode: str = "NON_TURBO"
) -> Dict[str, List[str]]:
    if ignore_stats is None:
        ignore_stats = []

    positives: List[str] = []
    negatives: List[str] = []
    tips: List[str] = []
    flags: List[str] = []
    used = set()

    hi = tags.get("highlight")
    lo = tags.get("lowlight")
    praises = tags.get("praises", [])
    critiques = tags.get("critiques", [])
    compound_flags = tags.get("compound_flags", [])

    # --- Praise ---
    candidates = [hi] + praises
    for stat in candidates:
        if not isinstance(stat, str):
            continue
        if not stat_allowed(stat, mode) or stat in ignore_stats:
            continue
        line = _choose_banded_line(stat, "positive", context)
        if line:
            positives.append(line)
            used.add(stat)
            break

    # --- Critique ---
    candidates = [lo] + critiques
    for stat in candidates:
        if not isinstance(stat, str):
            continue
        if not stat_allowed(stat, mode) or stat in ignore_stats or stat in used:
            continue
        line = _choose_banded_line(stat, "negative", context)
        if line:
            negatives.append(line)
            used.add(stat)
            break

    # --- Flag ---
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
        tip_line = _choose_banded_tip(stat, context, mode)
        if tip_line:
            tips.append(tip_line)
            break

    return {
        "positives": positives,
        "negatives": negatives,
        "flags": flags,
        "tips": tips
    }


# -------------------------
# Title selection (mirrored IMP bands)
# -------------------------

def _pick_title_bank(result_side: str, tier: str) -> List[str]:
    """
    Retrieve title lines for a given side ('win'|'loss') and tier.
    Falls back to legacy 'negative' bank if a new neg_* tier is missing.
    """
    side_book = TITLE_BOOK.get(result_side, {})
    if not isinstance(side_book, dict):
        return []
    lines = side_book.get(tier, [])
    if lines:
        return lines
    if tier in {"neg_low", "neg_mid", "neg_high", "neg_legendary"}:
        return side_book.get("negative", []) or []
    return lines or []


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

    # Very low neutral zone (−4 … +4) per your spec
    if -4 <= score_val <= 4:
        tier = "very_low"
        bank = _pick_title_bank("win" if won else "loss", tier)
        emoji = "🎲" if won else "💀"
        phrase = random.choice(bank) if bank else "played a game"
        return emoji, phrase

    # Positive bands
    if score_val >= 50:
        tier, win_emoji, loss_emoji = "legendary", "🧨", "🧨"
    elif score_val >= 35:
        tier, win_emoji, loss_emoji = "high", "💥", "💪"
    elif score_val >= 20:
        tier, win_emoji, loss_emoji = "mid", "🔥", "😓"
    elif score_val >= 5:
        tier, win_emoji, loss_emoji = "low", "🎯", "☠️"
    # Negative bands (mirrored)
    elif score_val <= -50:
        tier, win_emoji, loss_emoji = "neg_legendary", "🎁", "🤡"
    elif score_val <= -35:
        tier, win_emoji, loss_emoji = "neg_high", "🧯", "💀"
    elif score_val <= -20:
        tier, win_emoji, loss_emoji = "neg_mid", "🫠", "☠️"
    elif score_val <= -5:
        tier, win_emoji, loss_emoji = "neg_low", "😅", "😓"
    else:
        tier, win_emoji, loss_emoji = "very_low", "🎲", "💀"

    bank = _pick_title_bank("win" if won else "loss", tier)
    emoji = win_emoji if won else loss_emoji
    phrase = random.choice(bank) if bank else "played a game"
    return emoji, phrase
