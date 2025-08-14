# bot/runner.py

from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import (
    format_match_embed, build_discord_embed,
    format_fallback_embed, build_fallback_embed
)
from bot.config import CONFIG
from bot.throttle import throttle, throttle_webhook, set_webhook_cooldown
import requests
import json
import time

# Global flags for safety
_HARD_BLOCKED = False                  # Cloudflare 1015 detected
_PROCESS_COOLDOWN_UNTIL = 0.0          # Global "stop posting for a bit"

def _now() -> float:
    return time.monotonic()

def _process_cooldown_active() -> bool:
    return _now() < _PROCESS_COOLDOWN_UNTIL

def _set_process_cooldown(seconds: float):
    global _PROCESS_COOLDOWN_UNTIL
    try:
        seconds = max(1.0, float(seconds))
    except Exception:
        seconds = 5.0
    _PROCESS_COOLDOWN_UNTIL = _now() + seconds

def _looks_like_cloudflare_1015(response: requests.Response) -> bool:
    """Detect Cloudflare 'Error 1015' HTML page (IP rate limited)."""
    ctype = (response.headers.get("Content-Type") or "").lower()
    if "text/html" in ctype:
        body = (getattr(response, "text", "") or "")[:600].lower()
        # Common strings on the 1015 page
        return ("error 1015" in body) or ("you are being rate limited" in body and "cloudflare" in body)
    return False

def _parse_retry_after(response: requests.Response) -> float:
    """
    Parse backoff seconds from:
      • X-RateLimit-Reset-After (seconds)
      • Retry-After header (seconds)
      • JSON body retry_after (seconds; sometimes ms in bots API, guard for tiny values)
    """
    # Header: X-RateLimit-Reset-After
    try:
        xr = response.headers.get("X-RateLimit-Reset-After")
        if xr is not None:
            return max(0.5, float(xr))
    except Exception:
        pass

    # Header: Retry-After
    try:
        ra = response.headers.get("Retry-After")
        if ra is not None:
            return max(0.5, float(ra))
    except Exception:
        pass

    # JSON body: retry_after
    try:
        data = response.json()
        if isinstance(data, dict) and "retry_after" in data:
            val = float(data["retry_after"])
            # If the value is suspiciously small (<0.2), assume it's in seconds but from a ms-based client.
            # Clamp to 0.5s min and 60s max here; longer windows handled by headers.
            if 0 < val < 0.2:
                val = val * 1000.0  # be generous if it looked like milliseconds
            return max(0.5, min(val, 60.0))
    except Exception:
        pass

    # Fallback small backoff
    return 2.0

def post_to_discord_embed(embed: dict, webhook_url: str) -> bool:
    """
    Post a single embed to Discord with strict pacing and defensive handling.
    - Always calls throttle_webhook(webhook_url) before posting
    - Handles 429 with backoff; long backoffs trigger process/webhook cooldowns
    - Detects Cloudflare HTML block (Error 1015) and aborts the run
    """
    global _HARD_BLOCKED

    if _HARD_BLOCKED or _process_cooldown_active():
        return False

    # Per-webhook pacing guard (handles shared-IP bursts nicely)
    throttle_webhook(webhook_url)

    payload = {"embeds": [embed]}
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            # Success — lightly pace the next post as well
            throttle_webhook(webhook_url)
            return True

        # Hard 429
        if response.status_code == 429:
            backoff = _parse_retry_after(response)
            print(f"⚠️ Webhook 429 — retry_after={backoff:.2f}s")
            if backoff > 10:
                # Apply both a webhook-specific cooldown and a soft process cooldown
                set_webhook_cooldown(webhook_url, backoff)
                _set_process_cooldown(backoff)
                print(f"⏸️ Entering cooldown for {backoff:.2f}s due to long 429.")
                return False

            # Short backoff — sleep, pace, and single retry
            time.sleep(backoff)
            throttle_webhook(webhook_url)
            retry = requests.post(webhook_url, json=payload, timeout=10)
            if retry.status_code == 204:
                throttle_webhook(webhook_url)
                return True

            if _looks_like_cloudflare_1015(retry):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 encountered on retry — aborting run.")
                return False

            if retry.status_code == 429:
                rb = _parse_retry_after(retry)
                set_webhook_cooldown(webhook_url, rb)
                _set_process_cooldown(rb)
                print(f"⏸️ Secondary 429 — cooldown {rb:.2f}s.")
                return False

            print(f"⚠️ Retry failed {retry.status_code}: {retry.text[:200]}")
            return False

        # Cloudflare HTML/WAF detection on non-429
        if response.status_code in (403, 503) and _looks_like_cloudflare_1015(response):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block — aborting run.")
            return False

        print(f"⚠️ Webhook responded {response.status_code}: {response.text[:300]}")
        return False

    except Exception as e:
        print(f"❌ Failed to post embed to Discord: {e}")
        return False

def process_player(player_name: str, steam_id: int, last_posted_id: str | None, state: dict) -> bool:
    """Fetch and format the latest match for a player."""
    global _HARD_BLOCKED
    if _HARD_BLOCKED or _process_cooldown_active():
        return False

    throttle()  # Stratz-safe
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

    # If IMP missing, post a minimal fallback embed instead of skipping entirely
    if player_data.get("imp") is None:
        print(f"⏳ IMP not ready for match {match_id} (player {steam_id}). Posting minimal fallback embed.")
        try:
            result = format_fallback_embed(player_data, match_data, player_name)
            embed = build_fallback_embed(result)
            if CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
                posted = post_to_discord_embed(embed, CONFIG["webhook_url"])
                if posted:
                    print(f"✅ Posted fallback embed for {player_name} match {match_id}")
                    # Do NOT set state for fallback, so we pick up the full embed later.
                else:
                    print(f"⚠️ Failed to post fallback embed for {player_name} match {match_id}")
            else:
                print("⚠️ Webhook disabled or misconfigured — printing instead.")
                print(json.dumps(embed, indent=2))
            # Continue to next player either way
        except Exception as e:
            print(f"❌ Error formatting or posting fallback embed for {player_name}: {e}")
        return True

    print(f"🎮 {player_name} — processing match {match_id}")

    try:
        result = format_match_embed(player_data, match_data, player_data.get("stats", {}), player_name)
        embed = build_discord_embed(result)

        if CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
            posted = post_to_discord_embed(embed, CONFIG["webhook_url"])
            if posted:
                state[str(steam_id)] = match_id
                print(f"✅ Posted embed for {player_name} match {match_id}")
            else:
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

    for index, (player_name, steam_id) in enumerate(players.items(), start=1):
        if _HARD_BLOCKED:
            print("🧯 Ending run early due to Cloudflare hard block.")
            break
        if _process_cooldown_active():
            remaining = max(0.0, _PROCESS_COOLDOWN_UNTIL - _now())
            print(f"🧯 Ending run early — webhook cooling down for {remaining:.1f}s.")
            break

        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({steam_id})...")
        last_posted_id = state.get(str(steam_id))
        should_continue = process_player(player_name, steam_id, last_posted_id, state)
        if not should_continue:
            if _HARD_BLOCKED:
                print("🧯 Ending run early due to Cloudflare hard block.")
            elif _process_cooldown_active():
                remaining = max(0.0, _PROCESS_COOLDOWN_UNTIL - _now())
                print(f"🧯 Ending run early due to webhook cooldown ({remaining:.1f}s).")
            else:
                print("🧯 Ending run early to preserve API quota.")
            break

        # Gentle inter-player delay — avoid “first post after long idle” bursts
        time.sleep(0.6)

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
