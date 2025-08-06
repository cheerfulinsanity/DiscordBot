# bot/throttle.py

import time
from collections import deque

# Rolling tracker of timestamps for API calls
api_calls = deque()

# Stratz Free Tier Limits
MAX_CALLS_PER_SECOND = 20
MAX_CALLS_PER_MINUTE = 250
MAX_CALLS_PER_HOUR = 2000
# Note: No hard limit on daily quota enforced here

def throttle():
    while True:
        now = time.time()

        # Remove old entries (>1 hour, since we only enforce hourly/below)
        while api_calls and now - api_calls[0] > 3600:
            api_calls.popleft()

        # Count how many fall in each window
        count_1s   = sum(1 for t in api_calls if now - t <= 1)
        count_60s  = sum(1 for t in api_calls if now - t <= 60)
        count_3600 = len(api_calls)  # Already trimmed to last hour

        if count_1s >= MAX_CALLS_PER_SECOND:
            time.sleep(0.05)
            continue
        if count_60s >= MAX_CALLS_PER_MINUTE:
            time.sleep(1)
            continue
        if count_3600 >= MAX_CALLS_PER_HOUR:
            time.sleep(5)
            continue

        # Log call and return
        api_calls.append(now)
        return
