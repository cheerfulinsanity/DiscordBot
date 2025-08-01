# bot/throttle.py

import time
from collections import deque

api_calls = deque()

MAX_CALLS_PER_SECOND = 20
MAX_CALLS_PER_MINUTE = 250
MAX_CALLS_PER_HOUR = 2000
MAX_CALLS_PER_DAY = 10000

def throttle():
    now = time.time()

    while api_calls and now - api_calls[0] > 86400:
        api_calls.popleft()

    count_1s   = sum(1 for t in api_calls if now - t <= 1)
    count_60s  = sum(1 for t in api_calls if now - t <= 60)
    count_3600 = sum(1 for t in api_calls if now - t <= 3600)

    if count_1s >= MAX_CALLS_PER_SECOND:
        time.sleep(0.05)
        return throttle()
    if count_60s >= MAX_CALLS_PER_MINUTE:
        time.sleep(1)
        return throttle()
    if count_3600 >= MAX_CALLS_PER_HOUR:
        time.sleep(5)
        return throttle()
    if len(api_calls) >= MAX_CALLS_PER_DAY:
        raise RuntimeError("🛑 Daily API limit reached (10,000 calls)")

    api_calls.append(now)

