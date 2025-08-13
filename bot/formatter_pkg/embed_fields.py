# bot/formatter_pkg/embed_fields.py
from __future__ import annotations
from typing import Dict, List
from .helpers import seconds_to_mmss

def title_line(result: Dict[str, object]) -> str:
    hero = result.get("hero", "unknown")
    kda = result.get("kda", "0/0/0")
    victory = "Win" if result.get("isVictory") else "Loss"
    return f"{result.get('emoji', '')} {result.get('playerName', 'Player')} {result.get('title')} {kda} as {hero} — {victory}"

def build_fields(result: Dict[str, object]) -> List[Dict[str, object]]:
    duration = int(result.get("duration", 0))
    duration_str = seconds_to_mmss(duration)

    fields: List[Dict[str, object]] = [
        {
            "name": "🧮 Impact",
            "value": f"{float(result.get('score', 0.0)):.2f} (typical in-game: −10 to +10, high-end ~+20–30)",
            "inline": True,
        },
        {
            "name": "🧭 Role",
            "value": str(result.get("role", "unknown")).capitalize(),
            "inline": True,
        },
        {
            "name": "⚙️ Mode",
            "value": result.get("gameModeName", "Unknown"),
            "inline": True,
        },
        {
            "name": "⏱️ Duration",
            "value": duration_str,
            "inline": True,
        },
    ]

    if result.get("positives"):
        fields.append({
            "name": "🎯 What went well",
            "value": "\n".join(f"• {line}" for line in result["positives"]),
            "inline": False,
        })

    if result.get("negatives"):
        fields.append({
            "name": "🧱 What to work on",
            "value": "\n".join(f"• {line}" for line in result["negatives"]),
            "inline": False,
        })

    if result.get("flags"):
        fields.append({
            "name": "📌 Flagged behavior",
            "value": "\n".join(f"• {line}" for line in result["flags"]),
            "inline": False,
        })

    if result.get("tips"):
        fields.append({
            "name": "🗺️ Tips",
            "value": "\n".join(f"• {line}" for line in result["tips"]),
            "inline": False,
        })

    return fields
