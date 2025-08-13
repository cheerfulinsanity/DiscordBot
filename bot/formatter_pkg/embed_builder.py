from __future__ import annotations
from typing import Dict
from datetime import datetime, timezone
from .embed_fields import build_fields, title_line

def build_discord_embed(result: Dict[str, object]) -> Dict[str, object]:
    now = datetime.now(timezone.utc).astimezone()
    return {
        "title": title_line(result),
        "description": "",
        "fields": build_fields(result),
        "footer": {
            "text": f"Match ID: {result['matchId']} • {now.strftime('%b %d at %-I:%M %p')}"
        },
        "timestamp": now.isoformat(),
    }
