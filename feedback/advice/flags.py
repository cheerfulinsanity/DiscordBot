# feedback/advice/flags.py
import random
from typing import List, Optional
from feedback.catalog import COMPOUND_FLAGS

def select_flag_phrase(flags: List[str], mode: str) -> Optional[str]:
    """
    Deterministic behavior preserved (uses global RNG seeded upstream).
    First matching flag wins. Honors catalog 'modes' gating.
    """
    for flag in flags:
        if not isinstance(flag, str):
            continue
        entry = COMPOUND_FLAGS.get(flag)
        if not isinstance(entry, dict):
            continue
        allowed = entry.get("modes", ["ALL"])
        if "ALL" not in allowed and mode not in allowed:
            continue
        lines = entry.get("lines", [])
        if lines:
            return random.choice(lines)
    return None
