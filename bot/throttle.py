import time
import threading
from collections import deque

# Rolling tracker of timestamps for API calls (monotonic seconds)
api_calls = deque()
_lock = threading.Lock()

# Stratz Free Tier Limits
MAX_CALLS_PER_SECOND = 20
MAX_CALLS_PER_MINUTE = 250
MAX_CALLS_PER_HOUR = 2000

# Discord webhook limits (per webhook, not per bot user)
# Discord hard caps: ~30 requests/minute, burst bucket ~5 req / 2s
# We enforce tighter limits to keep a safe margin even during tests
discord_posts = deque()
_webhook_lock = threading.Lock()
MAX_DISCORD_POSTS_PER_MINUTE = 25  # safe buffer below 30/min
MAX_DISCORD_POSTS_PER_SECOND = 1   # no more than 1 post/sec
MIN_WEBHOOK_SPACING = 0.8          # minimum seconds between posts (jittered up to ~1.2s)

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

def throttle_webhook():
    """
    Rate limiter for Discord webhook posts.
    Enforces:
      • Max 25 posts/minute (rolling window)
      • Max 1 post/sec (burst bucket)
      • Minimum spacing of MIN_WEBHOOK_SPACING–1.2s between posts
    """
    import random
    while True:
        with _webhook_lock:
            now = _now()

            # Trim older than 60s
            cutoff_minute = now - 60.0
            while discord_posts and discord_posts[0] < cutoff_minute:
                discord_posts.popleft()

            sleep_for = 0.0

            # Enforce per-second burst cap
            threshold_1s = now - 1.0
            count_1s = sum(1 for t in discord_posts if t >= threshold_1s)
            if count_1s >= MAX_DISCORD_POSTS_PER_SECOND:
                earliest = min(t for t in discord_posts if t >= threshold_1s)
                sleep_for = max(sleep_for, (earliest + 1.0) - now)

            # Enforce per-minute rolling cap
            if len(discord_posts) >= MAX_DISCORD_POSTS_PER_MINUTE:
                earliest = discord_posts[0]
                sleep_for = max(sleep_for, (earliest + 60.0) - now)

            # Enforce minimum spacing between posts (extra jitter)
            if discord_posts:
                last_post_time = discord_posts[-1]
                min_next_time = last_post_time + MIN_WEBHOOK_SPACING + random.uniform(0.0, 0.4)
                if now < min_next_time:
                    sleep_for = max(sleep_for, min_next_time - now)

            if sleep_for <= 0:
                discord_posts.append(now)
                return

        time.sleep(min(sleep_for + 0.02, 5.0))
