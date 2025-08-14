# bot/runner_pkg/players.py

import json
import time
import os
from bot.fetch import get_latest_new_match
from bot.formatter import (
    format_match_embed,
    build_discord_embed,
    format_fallback_embed,
    build_fallback_embed,
)
from bot.config import CONFIG
from bot.throttle import throttle
from .webhook_client import (
    post_to_discord_embed,
    edit_discord_message,
    webhook_cooldown_active,
    is_hard_blocked,
    strip_query,
)


def _debug_level() -> int:
    raw = (os.getenv("DEBUG_MODE") or "0").strip().lower()
    try:
        return int(raw)
    except Exception:
        return 1 if raw in {"1", "true", "yes", "on"} else 0


def _truthy(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "on"}


def _force_fallback_for(steam_id: int) -> bool:
    """
    Test hook: force the fallback path even if IMP is ready.
    Active only when DEBUG_MODE > 0 and TEST_FORCE_FALLBACK is truthy.
    Optional scoping via TEST_FORCE_FALLBACK_ONLY_FOR=comma,separated,steam32Ids
    """
    if _debug_level() <= 0:
        return False
    if not _truthy(os.getenv("TEST_FORCE_FALLBACK")):
        return False

    allow = (os.getenv("TEST_FORCE_FALLBACK_ONLY_FOR") or "").strip()
    if not allow:
        return True

    allow_set: set[int] = set()
    for part in allow.split(","):
        part = part.strip()
        if part.isdigit():
            try:
                allow_set.add(int(part))
            except Exception:
                continue
    try:
        return int(steam_id) in allow_set
    except Exception:
        return False


def process_player(player_name: str, steam_id: int, last_posted_id: str | None, state: dict) -> bool:
    """Fetch and format the latest match for a player."""
    if is_hard_blocked():
        return False
    if webhook_cooldown_active():
        return False

    throttle()

    match_bundle = get_latest_new_match(steam_id, last_posted_id)
    if not match_bundle:
        print(f"⏩ No new match or failed to fetch for {player_name}. Skipping.")
        return True

    match_id = match_bundle["match_id"]
    match_data = match_bundle["full_data"]

    player_data = next((p for p in match_data["players"] if p.get("steamAccountId") == steam_id), None)
    if not player_data:
        print(f"❌ Player data missing in match {match_id} for {player_name}")
        return True

    # If there is a pending entry for this match, prefer editing that message when full stats are ready
    pending_map = state.setdefault("pending", {})
    pending_entry = pending_map.get(str(match_id))

    # --- Test hook: force fallback even if IMP is ready ---
    imp_value = player_data.get("imp")
    try:
        if _force_fallback_for(steam_id) and imp_value is not None:
            imp_value = None
            print(f"🧪 TEST_FORCE_FALLBACK active — forcing fallback for match {match_id} (player {steam_id}).")
    except Exception:
        pass

    if imp_value is None:
        print(f"⏳ IMP not ready for match {match_id} (player {steam_id}). Posting minimal fallback embed.")
        try:
            result = format_fallback_embed(player_data, match_data, player_name)
            embed = build_fallback_embed(result)
            if CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
                posted, msg_id = post_to_discord_embed(embed, CONFIG["webhook_url"], want_message_id=True)
                if posted:
                    print(f"✅ Posted fallback embed for {player_name} match {match_id}")
                    # Track for upgrade/expiry
                    pending_map[str(match_id)] = {
                        "steamId": steam_id,
                        "messageId": msg_id,
                        "postedAt": time.time(),
                        "webhookBase": strip_query(CONFIG["webhook_url"]),
                        "snapshot": result,  # enough to rebuild "expired" or provide name
                    }
                else:
                    if is_hard_blocked():
                        return False
                    if webhook_cooldown_active():
                        print("🧯 Ending run early due to webhook cooldown.")
                        return False
                    print(f"⚠️ Failed to post fallback embed for {player_name} match {match_id}")
            else:
                print("⚠️ Webhook disabled or misconfigured — printing instead.")
                print(json.dumps(embed, indent=2))
        except Exception as e:
            print(f"❌ Error formatting or posting fallback embed for {player_name}: {e}")
        return True

    print(f"🎮 {player_name} — processing match {match_id}")

    try:
        result = format_match_embed(player_data, match_data, player_data.get("stats", {}), player_name)
        embed = build_discord_embed(result)

        if pending_entry and pending_entry.get("messageId") and CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
            # Upgrade existing fallback message via edit
            ok = edit_discord_message(
                pending_entry["messageId"],
                embed,
                pending_entry.get("webhookBase") or CONFIG["webhook_url"],
            )
            if ok:
                print(f"🔁 Upgraded fallback → full embed for {player_name} match {match_id}")
                state[str(steam_id)] = match_id
                pending_map.pop(str(match_id), None)
            else:
                if is_hard_blocked():
                    return False
                if webhook_cooldown_active():
                    print("🧯 Ending run early due to webhook cooldown (during upgrade).")
                    return False
                print(f"⚠️ Failed to upgrade fallback for {player_name} match {match_id} — will retry later")
        else:
            # Normal fresh post path
            if CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
                posted, _ = post_to_discord_embed(embed, CONFIG["webhook_url"], want_message_id=False)
                if posted:
                    print(f"✅ Posted embed for {player_name} match {match_id}")
                    state[str(steam_id)] = match_id
                else:
                    if is_hard_blocked():
                        return False
                    if webhook_cooldown_active():
                        print("🧯 Ending run early due to webhook cooldown.")
                        return False
                    print(f"⚠️ Failed to post embed for {player_name} match {match_id}")
            else:
                print("⚠️ Webhook disabled or misconfigured — printing instead.")
                print(json.dumps(embed, indent=2))
                state[str(steam_id)] = match_id

    except Exception as e:
        print(f"❌ Error formatting or posting match for {player_name}: {e}")

    return True
