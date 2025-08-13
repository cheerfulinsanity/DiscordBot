"""
Compatibility shim that exposes the same public API while delegating to
the modular formatter package. Keeps imports elsewhere (runner, tests)
unchanged, and also re-exports constants from helpers to preserve
backwards compatibility.
"""
from .formatter_pkg import format_match_embed, build_discord_embed
from .formatter_pkg.helpers import NORMAL_STATS, TURBO_STATS

__all__ = [
    "format_match_embed",
    "build_discord_embed",
    "NORMAL_STATS",
    "TURBO_STATS",
]
