# bot/runner_pkg/webhook_client.py

import time
import random
import requests
from bot.throttle import throttle_webhook

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

    # 🔧 Pass the base webhook URL so per-webhook pacing groups correctly (matches monolith behavior)
    throttle_webhook(strip_query(webhook_url))

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
            throttle_webhook(strip_query(webhook_url))
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
    PATCH {webhookBase}/messages/{message_id} with {"embeds":[.]}
    """
    global _HARD_BLOCKED

    if _webhook_cooldown_active():
        return False

    # 🔧 Pass the base webhook URL so per-webhook pacing groups correctly
    throttle_webhook(strip_query(webhook_url))

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
            throttle_webhook(strip_query(webhook_url))
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


# --- Small public helpers for runner/orchestrator ---

def is_hard_blocked() -> bool:
    return _HARD_BLOCKED


def webhook_cooldown_active() -> bool:
    return _webhook_cooldown_active()


def webhook_cooldown_remaining() -> float:
    return max(0.0, _WEBHOOK_COOLDOWN_UNTIL - time.monotonic())
