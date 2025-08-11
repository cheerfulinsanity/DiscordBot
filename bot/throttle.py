# bot/throttle.py

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
# Note: No hard limit on daily quota enforced here

def _now() -> float:
    """Monotonic time in seconds to avoid system clock jumps."""
    return time.monotonic()

def throttle():
    """
    Global, process-wide rate limiter.
    Blocks until issuing another Stratz API call would respect all caps:
      - 20 per 1 second (sliding window)
      - 250 per 60 seconds (sliding window)
      - 2000 per 3600 seconds (sliding window)
    """
    while True:
        # Compute inside a lock to keep the deque consistent under concurrency
        with _lock:
            now = _now()

            # Trim anything older than 1 hour (we only enforce up to hourly)
            cutoff_hour = now - 3600.0
            while api_calls and api_calls[0] < cutoff_hour:
                api_calls.popleft()

            sleep_for = 0.0

            # --- Per-second window (20/sec)
            threshold_1s = now - 1.0
            # Count items in last 1s and track the earliest in-window timestamp
            count_1s = 0
            earliest_1s = None
            for t in api_calls:
                if t >= threshold_1s:
                    earliest_1s = t if earliest_1s is None else earliest_1s
                    count_1s += 1
            if count_1s >= MAX_CALLS_PER_SECOND and earliest_1s is not None:
                sleep_for = max(sleep_for, (earliest_1s + 1.0) - now)

            # --- Per-minute window (250/min)
            threshold_60s = now - 60.0
            count_60s = 0
            earliest_60s = None
            for t in api_calls:
                if t >= threshold_60s:
                    earliest_60s = t if earliest_60s is None else earliest_60s
                    count_60s += 1
            if count_60s >= MAX_CALLS_PER_MINUTE and earliest_60s is not None:
                sleep_for = max(sleep_for, (earliest_60s + 60.0) - now)

            # --- Per-hour window (2000/hr)
            count_3600 = len(api_calls)  # already trimmed to last hour
            if count_3600 >= MAX_CALLS_PER_HOUR and api_calls:
                earliest_3600 = api_calls[0]
                sleep_for = max(sleep_for, (earliest_3600 + 3600.0) - now)

            # If no wait needed, record this call and return immediately
            if sleep_for <= 0:
                api_calls.append(now)
                return

        # Sleep outside the lock so other threads can progress to compute their waits
        # Add a tiny epsilon and cap the maximum single sleep.
        time.sleep(min(sleep_for + 0.005, 5.0))
