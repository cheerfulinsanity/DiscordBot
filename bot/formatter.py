# bot/formatter.py

# Thin compatibility shim so the rest of the bot imports stay stable.
# The actual implementation now lives in bot/formatter_pkg/*.
from .formatter_pkg import format_match_embed, build_discord_embed

__all__ = ["format_match_embed", "build_discord_embed"]
