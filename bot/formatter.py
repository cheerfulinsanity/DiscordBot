# bot/formatter.py
"""
Compatibility shim that exposes the same public API while delegating to
the modular formatter package. Keeps imports elsewhere (runner, tests)
unchanged.
"""
from .formatter_pkg import format_match_embed, build_discord_embed

__all__ = ["format_match_embed", "build_discord_embed"]
