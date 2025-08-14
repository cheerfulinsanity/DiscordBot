import time
import threading
from collections import deque, defaultdict

# Stratz API limits (unchanged)
api_calls = deque()
_lock = threading.Lock()
MAX_CALLS_PER_SECOND = 20
MAX_CALLS_PER_MINUTE = 250
MAX_CALLS_PER_HOUR = 2000

def _now() -> float:
    """Monotonic time in seconds to avoid system clock jumps."""
    return time.monotonic()

def throttle():
    """
    Global, process-wide rate limiter for Stratz API calls.
    Blocks until issuing another Stratz API call would respect all caps.
    """
    while True:
        with _lock:
            now = _now()

            # Trim anything older than 1 hour
            cutoff_hour = now - 3600.0
            while api_calls and api_calls[0] < cutoff_hour:
                api_calls.popleft()

            sleep_for = 0.0

            # Per-second
            threshold_1s = now - 1.0
            count_1s = sum(1 for t in api_calls if t >= threshold_1s)
            if count_1s >= MAX_CALLS_PER_SECOND:
                earliest = min(t for t in api_calls if t >= threshold_1s)
                sleep_for = max(sleep_for, (earliest + 1.0) - now)

            # Per-minute
            threshold_60s = now - 60.0
            count_60s = sum(1 for t in api_calls if t >= threshold_60s)
            if count_60s >= MAX_CALLS_PER_MINUTE:
                earliest = min(t for t in api_calls if t >= threshold_60s)
                sleep_for = max(sleep_for, (earliest + 60.0) - now)

            # Per-hour
            if len(api_calls) >= MAX_CALLS_PER_HOUR:
                earliest = api_calls[0]
                sleep_for = max(sleep_for, (earliest + 3600.0) - now)

            if sleep_for <= 0:
                api_calls.append(now)
                return

        time.sleep(min(sleep_for + 0.005, 5.0))

# ----------------- Discord webhook pacing -----------------

# Per-webhook rolling windows and cooldowns
_webhook_posts: dict[str, deque] = defaultdict(deque)
_webhook_lock = threading.Lock()
# Conservative caps: Discord docs suggest ~30/min; on shared IPs that’s optimistic.
MAX_DISCORD_POSTS_PER_MINUTE = 15  # safer buffer
MAX_DISCORD_POSTS_PER_SECOND = 1   # never burst above 1/sec
MIN_WEBHOOK_SPACING_BASE = 2.8     # base spacing; we’ll add small jitter below

# Global slow-mode
_global_posts = deque()
GLOBAL_MIN_SPACING_BASE = 3.5  # base delay between ANY posts
GLOBAL_JITTER = 1.0            # add up to +1s jitter

# Optional external cooldowns (e.g., from a 429 Retry-After). Runner can set these.
_webhook_cooldown_until: dict[str, float] = defaultdict(float)

def set_webhook_cooldown(webhook_url: str, seconds: float):
    """Allow caller to force a cooldown for a specific webhook."""
    try:
        seconds = max(1.0, float(seconds))
    except Exception:
        seconds = 3.0
    with _webhook_lock:
        _webhook_cooldown_until[webhook_url] = _now() + seconds

def throttle_webhook(webhook_url: str):
    """
    Rate limiter for Discord webhook posts (per webhook URL + global).
    Enforces:
      • Global min spacing between any posts (~3.5–4.5s)
      • Max 15 posts/minute (rolling window) per webhook
      • Max 1 post/sec per webhook
      • Minimum spacing of ~2.8–3.6s between posts per webhook
      • Honors externally imposed cooldowns via set_webhook_cooldown()
    """
    import random
    while True:
        with _webhook_lock:
            now = _now()

            # Respect externally imposed cooldowns
            until = _webhook_cooldown_until.get(webhook_url, 0.0)
            if now < until:
                sleep_for = until - now
            else:
                sleep_for = 0.0

                # --- Global spacing ---
                if _global_posts:
                    min_next_global = _global_posts[-1] + GLOBAL_MIN_SPACING_BASE + random.uniform(0.0, GLOBAL_JITTER)
                    if now < min_next_global:
                        sleep_for = max(sleep_for, min_next_global - now)

                # --- Per-webhook checks ---
                posts = _webhook_posts[webhook_url]

                # Trim older than 60s
                cutoff_minute = now - 60.0
                while posts and posts[0] < cutoff_minute:
                    posts.popleft()

                # Per-second burst cap
                threshold_1s = now - 1.0
                count_1s = sum(1 for t in posts if t >= threshold_1s)
                if count_1s >= MAX_DISCORD_POSTS_PER_SECOND:
                    earliest = min(t for t in posts if t >= threshold_1s)
                    sleep_for = max(sleep_for, (earliest + 1.0) - now)

                # Per-minute rolling cap
                if len(posts) >= MAX_DISCORD_POSTS_PER_MINUTE:
                    earliest = posts[0]
                    sleep_for = max(sleep_for, (earliest + 60.0) - now)

                # Minimum per-webhook spacing + jitter
                if posts:
                    last_post_time = posts[-1]
                    min_next_time = last_post_time + MIN_WEBHOOK_SPACING_BASE + random.uniform(0.0, 0.8)
                    if now < min_next_time:
                        sleep_for = max(sleep_for, min_next_time - now)

            if sleep_for <= 0:
                now = _now()
                _global_posts.append(now)
                _webhook_posts[webhook_url].append(now)
                return

        time.sleep(min(sleep_for + 0.02, 5.0))
