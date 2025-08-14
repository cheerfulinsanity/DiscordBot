# bot/runner.py

from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import format_match_embed, build_discord_embed
from bot.config import CONFIG
from bot.throttle import throttle, throttle_webhook  # ✅ Added throttle_webhook
import requests
import json
import time  # ✅ Added for inter-player delay
import random  # ✅ Jitter for post pacing

# Global flag to stop the run if Cloudflare hard-blocks our IP
_HARD_BLOCKED = False


def _parse_retry_after(response: requests.Response) -> float:
    """Parse backoff seconds from Retry-After header or Discord JSON."""
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
            if val_f > 0 and val_f < 0.2:
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


def post_to_discord_embed(embed: dict, webhook_url: str) -> bool:
    """
    Post a single embed to Discord with safe handling:
      • Respect 429 with Retry-After / retry_after.
      • Detect Cloudflare 1015 HTML and mark hard-block.
      • Throttle per webhook to avoid hitting limits.
      • Skip overly long backoffs (>10s).
    """
    global _HARD_BLOCKED

    # ✅ Webhook rate limiter before posting
    throttle_webhook()

    payload = {"embeds": [embed]}
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return True

        if response.status_code == 429:
            backoff = _parse_retry_after(response)
            print(f"⚠️ Rate limited by Discord — retry_after = {backoff:.2f}s (raw)")
            if backoff > 10:
                print(f"⏩ Backoff {backoff:.2f}s too long — skipping this player for now.")
                return False
            time.sleep(backoff)
            retry = requests.post(webhook_url, json=payload, timeout=10)
            if retry.status_code == 204:
                time.sleep(1.0 + random.uniform(0.1, 0.6))
                return True
            if _looks_like_cloudflare_1015(retry):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 encountered on retry — aborting run to cool down.")
                return False
            print(f"⚠️ Retry failed with status {retry.status_code}: {retry.text[:200]}")
            return False

        if response.status_code in (403, 429) and _looks_like_cloudflare_1015(response):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block detected — aborting run to cool down.")
            return False

        print(f"⚠️ Discord webhook responded {response.status_code}: {response.text[:300]}")
        return False

    except Exception as e:
        print(f"❌ Failed to post embed to Discord: {e}")
        return False


def process_player(player_name: str, steam_id: int, last_posted_id: str | None, state: dict) -> bool:
    """Fetch and format the latest match for a player."""
    global _HARD_BLOCKED
    if _HARD_BLOCKED:
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

    if player_data.get("imp") is None:
        print(f"⏳ IMP not ready for match {match_id} (player {steam_id}). Skipping for now; will retry on next run.")
        return True

    print(f"🎮 {player_name} — processing match {match_id}")

    try:
        result = format_match_embed(player_data, match_data, player_data.get("stats", {}), player_name)
        embed = build_discord_embed(result)

        if CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
            posted = post_to_discord_embed(embed, CONFIG["webhook_url"])
            if posted:
                print(f"✅ Posted embed for {player_name} match {match_id}")
                state[str(steam_id)] = match_id
            else:
                if _HARD_BLOCKED:
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

    for index, (player_name, steam_id) in enumerate(players.items(), start=1):
        if _HARD_BLOCKED:
            print("🧯 Ending run early due to Cloudflare hard block.")
            break

        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({steam_id})...")
        last_posted_id = state.get(str(steam_id))
        should_continue = process_player(player_name, steam_id, last_posted_id, state)
        if not should_continue:
            if _HARD_BLOCKED:
                print("🧯 Ending run early due to Cloudflare hard block.")
            else:
                print("🧯 Ending run early to preserve API quota.")
            break
        time.sleep(0.2)  # Soft cooldown between players

    save_state(state)
    print("📝 Updated state.json on GitHub Gist")
    print("✅ GuildBot run complete.")
