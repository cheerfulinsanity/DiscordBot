from bot.throttle import throttle, throttle_webhook  # ✅ added throttle_webhook

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
