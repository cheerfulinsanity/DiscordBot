# bot/runner.py

from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import format_match_embed, build_discord_embed, format_fallback_embed, build_fallback_embed  # ✅ Added fallback functions
from bot.config import CONFIG
from bot.throttle import throttle, throttle_webhook  # ✅ Added throttle_webhook
from bot.stratz import fetch_full_match  # ✅ For upgrade pass by matchId
import requests
import json
import time  # ✅ Added for inter-player delay
import random  # ✅ Jitter for post pacing

# --- Constants ---
PENDING_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours

# Global flag to stop the run if Cloudflare hard-blocks our IP
_HARD_BLOCKED = False
# Global cooldown (monotonic seconds) for Discord webhook bucket
_WEBHOOK_COOLDOWN_UNTIL = 0.0


def _parse_retry_after(response: requests.Response) -> float:
    """Parse backoff seconds from Retry-After header, JSON, or X-RateLimit-Reset-After."""
    try:
        xr = response.headers.get("X-RateLimit-Reset-After")
        if xr is not None:
            return max(0.5, float(xr))
    except Exception:
        pass

    ra = response.headers.get("Retry-After")
    if ra:
        try:
            return max(0.5, float(ra))
        except Exception:
            pass
    try:
        data = response.json()
        if isinstance(data, dict) and "retry_after" in data:
            val_f = float(data.get("retry_after"))
            # Some Discord responses use ms; heuristic guard
            if val_f > 60:
                val_f = val_f / 1000.0
            elif 0 < val_f < 0.2:
                val_f = val_f * 1000.0
            return max(0.5, min(val_f, 60.0))
    except Exception:
        pass
    return 2.0


def _looks_like_cloudflare_1015(response: requests.Response) -> bool:
    """Detect Cloudflare Error 1015 HTML block."""
    if "text/html" in (response.headers.get("Content-Type") or "").lower():
        body = (response.text or "")[:500].lower()
        return "error 1015" in body or "you are being rate limited" in body or "cloudflare" in body
    return False


def _webhook_cooldown_active() -> bool:
    return time.monotonic() < _WEBHOOK_COOLDOWN_UNTIL


def _set_webhook_cooldown(seconds: float):
    global _WEBHOOK_COOLDOWN_UNTIL
    seconds = max(1.0, float(seconds))
    _WEBHOOK_COOLDOWN_UNTIL = time.monotonic() + seconds


def _add_wait_param(url: str) -> str:
    """Ensure ?wait=true so Discord returns a JSON body (message object)."""
    return url + ("&wait=true" if "?" in url else "?wait=true")


def strip_query(url: str) -> str:
    """Return webhook base without any query params."""
    q = url.find("?")
    return url if q == -1 else url[:q]


def post_to_discord_embed(embed: dict, webhook_url: str, want_message_id: bool = False) -> tuple[bool, str | None]:
    """
    Post a single embed to Discord with safe handling:
      • Respect 429 with Retry-After / reset-after.
      • Detect Cloudflare 1015 HTML and mark hard-block.
      • Throttle per webhook to avoid hitting limits.
      • Abort run on long cooldowns (set global cooldown).
    Returns (success, message_id) — message_id may be None if not requested or if 204/No Content.
    """
    global _HARD_BLOCKED

    if _webhook_cooldown_active():
        remaining = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
        print(f"⏸️ Webhook cooling down — {remaining:.1f}s remaining. Skipping post.")
        return (False, None)

    throttle_webhook()

    url = _add_wait_param(webhook_url) if want_message_id else webhook_url
    payload = {"embeds": [embed]}
    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 204:
            # No body returned (typical when wait=false). Success.
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return (True, None)

        if response.status_code == 200:
            # wait=true → JSON body; capture id if requested
            msg_id = None
            if want_message_id:
                try:
                    msg = response.json()
                    msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                except Exception:
                    msg_id = None
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return (True, msg_id)

        if response.status_code == 429:
            backoff = _parse_retry_after(response)
            print(f"⚠️ Rate limited by Discord — retry_after = {backoff:.2f}s (raw)")
            if backoff > 10:
                _set_webhook_cooldown(backoff)
                print(f"⏩ Backoff {backoff:.2f}s too long — entering global cooldown and skipping further posts.")
                return (False, None)
            time.sleep(backoff)
            throttle_webhook()
            retry = requests.post(url, json=payload, timeout=10)
            if retry.status_code in (200, 204):
                msg_id = None
                if want_message_id and retry.status_code == 200:
                    try:
                        msg = retry.json()
                        msg_id = str(msg.get("id")) if isinstance(msg, dict) else None
                    except Exception:
                        msg_id = None
                time.sleep(1.0 + random.uniform(0.1, 0.6))
                return (True, msg_id)
            if _looks_like_cloudflare_1015(retry):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 encountered on retry — aborting run to cool down.")
                return (False, None)
            if retry.status_code == 429:
                rb = _parse_retry_after(retry)
                _set_webhook_cooldown(max(backoff, rb))
                print(f"⏩ Secondary 429 — entering global cooldown for {max(backoff, rb):.2f}s.")
                return (False, None)
            print(f"⚠️ Retry failed with status {retry.status_code}: {retry.text[:200]}")
            return (False, None)

        if response.status_code in (403, 429) and _looks_like_cloudflare_1015(response):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block detected — aborting run to cool down.")
            return (False, None)

        print(f"⚠️ Discord webhook responded {response.status_code}: {response.text[:300]}")
        return (False, None)

    except Exception as e:
        print(f"❌ Failed to post embed to Discord: {e}")
        return (False, None)


def edit_discord_message(message_id: str, embed: dict, webhook_url: str) -> bool:
    """
    Edit a previously-sent webhook message by ID.
    PATCH {webhookBase}/messages/{message_id} with {"embeds":[...]}
    """
    global _HARD_BLOCKED

    if _webhook_cooldown_active():
        return False

    throttle_webhook()

    base = strip_query(webhook_url)
    url = f"{base}/messages/{message_id}"
    payload = {"embeds": [embed]}

    try:
        response = requests.patch(url, json=payload, timeout=10)
        if response.status_code in (200, 204):
            time.sleep(0.6 + random.uniform(0.05, 0.3))
            return True
        if response.status_code == 429:
            backoff = _parse_retry_after(response)
            print(f"⚠️ Edit rate limited — retry_after = {backoff:.2f}s")
            if backoff > 10:
                _set_webhook_cooldown(backoff)
                return False
            time.sleep(backoff)
            throttle_webhook()
            retry = requests.patch(url, json=payload, timeout=10)
            if retry.status_code in (200, 204):
                return True
            if _looks_like_cloudflare_1015(retry):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 encountered on edit retry — aborting run.")
                return False
            return False
        if _looks_like_cloudflare_1015(response):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block on edit — aborting run.")
            return False
        print(f"⚠️ Edit failed {response.status_code}: {response.text[:300]}")
        return False
    except Exception as e:
        print(f"❌ Edit request failed: {e}")
        return False


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
    global _HARD_BLOCKED
    if _HARD_BLOCKED:
        return False

    pending_map = state.setdefault("pending", {})
    if not pending_map:
        return True

    now = time.time()
    items = list(pending_map.items())

    for match_id_str, entry in items:
        if _HARD_BLOCKED or _webhook_cooldown_active():
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
                        if _HARD_BLOCKED or _webhook_cooldown_active():
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
                    if _HARD_BLOCKED or _webhook_cooldown_active():
                        return False
                    print(f"⚠️ Failed to upgrade (edit) for match {match_id} — will retry later")
            except Exception as e:
                print(f"❌ Error building/upgrading embed for match {match_id}: {e}")
                # Leave pending for retry

        # Pace between items to be gentle on Discord + Stratz
        time.sleep(0.5)

    return True


def process_player(player_name: str, steam_id: int, last_posted_id: str | None, state: dict) -> bool:
    """Fetch and format the latest match for a player."""
    global _HARD_BLOCKED
    if _HARD_BLOCKED:
        return False
    if _webhook_cooldown_active():
        return False

    throttle()
    match_bundle = get_latest_new_match(steam_id, last_posted_id)

    if isinstance(match_bundle, dict) and match_bundle.get("error") == "quota_exceeded":
        print(f"🛑 Skipping remaining players — quota exceeded.")
        return False

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

    if player_data.get("imp") is None:
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
                    if _HARD_BLOCKED:
                        return False
                    if _webhook_cooldown_active():
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
            ok = edit_discord_message(pending_entry["messageId"], embed, pending_entry.get("webhookBase") or CONFIG["webhook_url"])
            if ok:
                print(f"🔁 Upgraded fallback → full embed for {player_name} match {match_id}")
                state[str(steam_id)] = match_id
                pending_map.pop(str(match_id), None)
            else:
                if _HARD_BLOCKED:
                    return False
                if _webhook_cooldown_active():
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
                    if _HARD_BLOCKED:
                        return False
                    if _webhook_cooldown_active():
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


def run_bot():
    global _HARD_BLOCKED
    print("🚀 GuildBot started")

    players = CONFIG["players"]
    print(f"👥 Loaded {len(players)} players from config.json")

    state = load_state()
    print("📥 Loaded state.json from GitHub Gist")

    # Pass 0: try to upgrade or expire existing fallbacks before scanning for new matches
    ok = process_pending_upgrades_and_expiry(state)
    if not ok:
        if _HARD_BLOCKED:
            print("🧯 Ending run early due to Cloudflare hard block.")
        elif _webhook_cooldown_active():
            remaining = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
            print(f"🧯 Ending run early — webhook cooling down for {remaining:.1f}s.")
        else:
            print("🧯 Ending run early to preserve API quota.")
        save_state(state)
        print("📝 Updated state.json on GitHub Gist")
        print("✅ GuildBot run complete.")
        return

    for index, (player_name, steam_id) in enumerate(players.items(), start=1):
        if _HARD_BLOCKED:
            print("🧯 Ending run early due to Cloudflare hard block.")
            break
        if _webhook_cooldown_active():
            remaining = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
            print(f"🧯 Ending run early — webhook cooling down for {remaining:.1f}s.")
            break

        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({steam_id})...")
        last_posted_id = state.get(str(steam_id))
        should_continue = process_player(player_name, steam_id, last_posted_id, state)
        if not should_continue:
            if _HARD_BLOCKED:
                print("🧯 Ending run early due to Cloudflare hard block.")
            elif _webhook_cooldown_active():
                remaining = max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
                print(f"🧯 Ending run early due to webhook cooldown ({remaining:.1f}s).")
            else:
                print("🧯 Ending run early to preserve API quota.")
            break
        time.sleep(0.6)

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
