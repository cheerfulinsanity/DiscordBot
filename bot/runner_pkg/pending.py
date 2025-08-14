# bot/runner_pkg/pending.py

import time
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

# --- Constants ---
PENDING_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours


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

        # Expiry check
        posted_at = float(entry.get("postedAt") or 0)
        if posted_at and (now - posted_at) >= PENDING_EXPIRY_SECONDS:
            print(f"⏳ Pending match {match_id} expired — marking message and removing from state.")
            try:
                if CONFIG.get("webhook_enabled") and webhook_base and message_id:
                    expired_embed = _expire_pending_entry(entry)
                    ok = edit_discord_message(message_id, expired_embed, webhook_base)
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
            continue

        if player_data.get("imp") is not None and CONFIG.get("webhook_enabled") and webhook_base and message_id:
            try:
                # Build full embed and edit in place
                snap = entry.get("snapshot") or {}
                display_name = snap.get("playerName", "Player")
                result = format_match_embed(player_data, full, player_data.get("stats", {}), display_name)
                embed = build_discord_embed(result)
                ok = edit_discord_message(message_id, embed, webhook_base)
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
