from bot.fetch import get_latest_new_match
from bot.gist_state import load_state, save_state
from bot.formatter import format_match_embed, build_discord_embed
from bot.config import CONFIG
from bot.throttle import throttle, throttle_webhook  # ✅ added webhook throttle
import requests
import json
import time
import random

# Global flag to stop the run if Cloudflare hard-blocks our IP
_HARD_BLOCKED = False


def _parse_retry_after(response: requests.Response) -> float:
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
    if "text/html" in (response.headers.get("Content-Type") or "").lower():
        body = (response.text or "")[:500].lower()
        return "error 1015" in body or "you are being rate limited" in body or "cloudflare" in body
    return False


def post_to_discord_embed(embed: dict, webhook_url: str) -> bool:
    global _HARD_BLOCKED
    payload = {"embeds": [embed]}
    try:
        # ✅ Always rate-limit webhook calls before sending
        throttle_webhook()

        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            time.sleep(1.0 + random.uniform(0.1, 0.6))
            return True

        if response.status_code == 429:
            backoff = _parse_retry_after(response)
            print(f"⚠️ Rate limited by Discord — retry_after = {backoff:.2f}s (raw)", flush=True)

            # ✅ Cap absurd delays to skip instead of freezing
            if backoff > 15:
                print(f"⏩ Backoff {backoff:.2f}s too long — skipping this player for now.", flush=True)
                return False

            time.sleep(backoff)
            retry = requests.post(webhook_url, json=payload, timeout=10)
            if retry.status_code == 204:
                time.sleep(1.0 + random.uniform(0.1, 0.6))
                return True
            if _looks_like_cloudflare_1015(retry):
                _HARD_BLOCKED = True
                print("🛑 Cloudflare 1015 encountered on retry — aborting run to cool down.", flush=True)
                return False
            print(f"⚠️ Retry failed with status {retry.status_code}: {retry.text[:200]}", flush=True)
            return False

        if response.status_code in (403, 429) and _looks_like_cloudflare_1015(response):
            _HARD_BLOCKED = True
            print("🛑 Cloudflare 1015 HTML block detected — aborting run to cool down.", flush=True)
            return False

        print(f"⚠️ Discord webhook responded {response.status_code}: {response.text[:300]}", flush=True)
        return False

    except Exception as e:
        print(f"❌ Failed to post embed to Discord: {e}", flush=True)
        return False


def process_player(player_name: str, steam_id: int, last_posted_id: str | None, state: dict) -> bool:
    global _HARD_BLOCKED

    if _HARD_BLOCKED:
        return False

    throttle()
    match_bundle = get_latest_new_match(steam_id, last_posted_id)

    if isinstance(match_bundle, dict) and match_bundle.get("error") == "quota_exceeded":
        print(f"🛑 Skipping remaining players — quota exceeded.", flush=True)
        return False

    if not match_bundle:
        print(f"⏩ No new match or failed to fetch for {player_name}. Skipping.", flush=True)
        return True

    match_id = match_bundle["match_id"]
    match_data = match_bundle["full_data"]

    player_data = next(
        (p for p in match_data["players"] if p.get("steamAccountId") == steam_id),
        None
    )
    if not player_data:
        print(f"❌ Player data missing in match {match_id} for {player_name}", flush=True)
        return True

    if player_data.get("imp") is None:
        print(f"⏳ IMP not ready for match {match_id} (player {steam_id}). Skipping for now; will retry on next run.", flush=True)
        return True

    print(f"🎮 {player_name} — processing match {match_id}", flush=True)

    try:
        result = format_match_embed(player_data, match_data, player_data.get("stats", {}), player_name)
        embed = build_discord_embed(result)

        if CONFIG.get("webhook_enabled") and CONFIG.get("webhook_url"):
            posted = post_to_discord_embed(embed, CONFIG["webhook_url"])
            if posted:
                print(f"✅ Posted embed for {player_name} match {match_id}", flush=True)
                state[str(steam_id)] = match_id
            else:
                if _HARD_BLOCKED:
                    return False
                print(f"⚠️ Failed to post embed for {player_name} match {match_id}", flush=True)
        else:
            print("⚠️ Webhook disabled or misconfigured — printing instead.", flush=True)
            print(json.dumps(embed, indent=2), flush=True)
            state[str(steam_id)] = match_id

    except Exception as e:
        print(f"❌ Error formatting or posting match for {player_name}: {e}", flush=True)

    return True


def run_bot():
    global _HARD_BLOCKED
    _HARD_BLOCKED = False  # ✅ Reset block flag each run

    print("🚀 GuildBot started", flush=True)

    players = CONFIG["players"]
    print(f"👥 Loaded {len(players)} players from config.json", flush=True)

    state = load_state()
    print("📥 Loaded state.json from GitHub Gist", flush=True)

    for index, (player_name, steam_id) in enumerate(players.items(), start=1):
        if _HARD_BLOCKED:
            print("🧯 Ending run early due to Cloudflare hard block.", flush=True)
            break

        print(f"🔍 [{index}/{len(players)}] Checking {player_name} ({steam_id})...", flush=True)
        last_posted_id = state.get(str(steam_id))
        should_continue = process_player(player_name, steam_id, last_posted_id, state)
        if not should_continue:
            if _HARD_BLOCKED:
                print("🧯 Ending run early due to Cloudflare hard block.", flush=True)
            else:
                print("🧯 Ending run early to preserve API quota.", flush=True)
            break
        time.sleep(0.2)

    save_state(state)
    print("📝 Updated state.json on GitHub Gist", flush=True)
    print("✅ GuildBot run complete.", flush=True)
