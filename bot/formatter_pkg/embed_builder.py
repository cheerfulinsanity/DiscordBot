# bot/formatter_pkg/embed_builder.py
from __future__ import annotations
from typing import Dict
from datetime import datetime, timezone
from .embed_fields import build_fields, title_line

class EmbedBuilder:
    def __init__(self, result: Dict[str, object]) -> None:
        self.result = result
        self._fields = build_fields(result)

    def as_embed(self) -> Dict[str, object]:
        now = datetime.now(timezone.utc).astimezone()
        return {
            "title": title_line(self.result),
            "description": "",
            "fields": self._fields,
            "footer": {
                "text": f"Match ID: {self.result['matchId']} • {now.strftime('%b %d at %-I:%M %p')}"
            },
            "timestamp": now.isoformat(),
        }

def build_discord_embed(result: Dict[str, object]) -> Dict[str, object]:
    return EmbedBuilder(result).as_embed()
