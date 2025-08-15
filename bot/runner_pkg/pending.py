# bot/runner_pkg/pending.py

import time
import os
from bot.config import CONFIG
from bot.throttle import throttle
from bot.stratz import fetch_full_match
from bot.formatter import (
    format_match_embed,
    build_discord_embed,
    build_fallback_embed,
)
from .webhook_client import (
    edit_discord_message,
    strip_query,
    webhook_cooldown_active,
    is_hard_blocked,
)

# --- Defaults & bounds ---
# Historical default was 24h; we now honor an env override with a default of 12h.
# Bounds protect against misconfiguration (30m–48h).
PENDING_EXPIRY_SECONDS = 24 * 60 * 60  # legacy constant (fallback only)
_MIN_EXPIRY = 30 * 60                  # 30 minutes
_MAX_EXPIRY = 48 * 60 * 60            # 48 hours
_DEFAULT_EXPIRY = 12 * 60 * 60        # 12 hours


def _env_expiry_seconds() -> int:
    """Resolve expiry seconds from env with sane bounds, falling back to 12h."""
    raw = (os.getenv("PENDING_EXPIRY_SEC") or "").strip()
    if raw.isdigit():
        try:
            v = int(raw)
            return max(_MIN_EXPIRY, min(_MAX_EXPIRY, v))
        except Exception:
            pass
    return _DEFAULT_EXPIRY


def _entry_expiry_seconds(entry: dict) -> int:
    """
    Determine the expiry for a specific pending entry:
      1) entry['expiresAfterSec'] if present (bounded)
      2) env PENDING_EXPIRY_SEC (bounded)
      3) legacy constant PENDING_EXPIRY_SECONDS (bounded to max/min for safety)
    """
    try:
        v = int(entry.get("expiresAfterSec"))
        return max(_MIN_EXPIRY, min(_MAX_EXPIRY, v))
    except Exception:
        pass

    # Env override
    env_v = _env_expiry_seconds()
    if env_v:
        return env_v

    # Legacy fallback (kept for backward compatibility)
    try:
        return max(_MIN_EXPIRY, min(_MAX_EXPIRY, int(PENDING_EXPIRY_SECONDS)))
    except Exception:
        return _DEFAULT_EXPIRY


def _expire_pending_entry(entry: dict) -> dict:
    """Build an 'expired' version of the fallback embed from stored snapshot."""
    snap = entry.get("snapshot") or {}
    expired = dict(snap)
    expired["emoji"] = "⌛"
    expired["title"] = "(Expired — no IMP)"
    expired["statusNote"] = "Expired — Stratz did not parse this match in time."
    return build_fallback_embed(expired)


def process_pending_upgrades_and_expiry(state: dict) -> bool:
    """
    Pass 0: try to upgrade or expire any pending fallback messages.
    Returns False to signal the run should end early (e.g., cooldown/hard-block).
    """
    if is_hard_blocked():
        return False

    pending_map = state.setdefault("pending", {})
    if not pending_map:
        return True

    now = time.time()
    items = list(pending_map.items())

    for match_id_str, entry in items:
        if is_hard_blocked() or webhook_cooldown_active():
            return False

        try:
            match_id = int(match_id_str)
        except Exception:
            # Bad key — drop it
            pending_map.pop(match_id_str, None)
            continue

        steam_id = entry.get("steamId")
        webhook_base = entry.get("webhookBase") or CONFIG.get("webhook_url")
        message_id = entry.get("messageId")

        # Expiry check (per-entry or env-driven)
        posted_at = float(entry.get("postedAt") or 0)
        expiry_seconds = _entry_expiry_seconds(entry)
        if posted_at and (now - posted_at) >= expiry_seconds:
            print(f"⏳ Pending match {match_id} expired — marking message and removing from state.")
            try:
                if CONFIG.get("webhook_enabled") and webhook_base and message_id:
                    expired_embed = _expire_pending_entry(entry)
                    ok = edit_discord_message(message_id, expired_embed, webhook_base, exact_base=True)  # ✅
                    if not ok:
                        if is_hard_blocked() or webhook_cooldown_active():
                            return False
                        print(f"⚠️ Failed to mark expired for match {match_id} — will retry next run")
                        continue
                # Remove from pending after attempting expiry
                pending_map.pop(match_id_str, None)
            except Exception as e:
                print(f"❌ Error expiring pending match {match_id}: {e}")
                pending_map.pop(match_id_str, None)
            continue

        # Try to upgrade — re-fetch match and check IMP
        throttle()
        full = fetch_full_match(match_id)
        if not full:
            # transient miss — skip this one for now
            time.sleep(0.5)
            continue
        if isinstance(full, dict) and full.get("error") == "quota_exceeded":
            print("🛑 Quota exceeded during pending upgrade pass — aborting early.")
            return False

        player_data = None
        for p in (full.get("players") or []):
            if p.get("steamAccountId") == steam_id:
                player_data = p
                break
        if not player_data:
            time.sleep(0.5)
            continue

        if player_data.get("imp") is not None and CONFIG.get("webhook_enabled") and webhook_base and message_id:
            try:
                # Build full embed and edit in place
                snap = entry.get("snapshot") or {}
                display_name = snap.get("playerName", "Player")
                result = format_match_embed(player_data, full, player_data.get("stats", {}), display_name)
                embed = build_discord_embed(result)
                ok = edit_discord_message(message_id, embed, webhook_base, exact_base=True)  # ✅
                if ok:
                    print(f"🔁 Upgraded fallback → full embed for match {match_id} (steam {steam_id})")
                    state[str(steam_id)] = match_id
                    pending_map.pop(match_id_str, None)
                else:
                    if is_hard_blocked() or webhook_cooldown_active():
                        return False
                    print(f"⚠️ Failed to upgrade (edit) for match {match_id} — will retry later")
            except Exception as e:
                print(f"❌ Error building/upgrading embed for match {match_id}: {e}")
                # Leave pending for retry

        # Pace between items to be gentle on Discord + Stratz
        time.sleep(0.5)

    return True
