# bot/stratz.py

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import requests
from requests import Response
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError

from bot.throttle import throttle  # ✅ Enforce rate limit before each request

STRATZ_GRAPHQL_URL = "https://api.stratz.com/graphql"

# Reuse one session across calls to reduce connection overhead
_SESSION = requests.Session()


def _is_quota_exceeded(resp: Optional[Response], exc: Optional[BaseException]) -> bool:
    """
    Heuristic to identify quota/rate-limit conditions.
    """
    if resp is not None and resp.status_code == 429:
        return True
    if exc and "quota" in str(exc).lower():
        return True
    return False


def _log_graphql_errors(payload: Dict[str, Any]) -> None:
    """
    If a GraphQL 'errors' array is present, log the first one for visibility.
    """
    try:
        errors = payload.get("errors")
        if errors and isinstance(errors, list):
            first = errors[0]
            msg = first.get("message") or str(first)
            print(f"⚠️ GraphQL error: {msg}")
    except Exception:
        # Logging should never raise
        pass


def _request_with_retry(
    *,
    query: str,
    variables: Dict[str, Any],
    headers: Dict[str, str],
    timeout: int,
    max_retries: int = 1,
) -> Optional[Response]:
    """
    Do a POST to Stratz with up to 1 retry on transient network/5xx errors.
    Never retries on 429 (quota) to avoid wasting budget.
    """
    attempt = 0
    last_exc: Optional[BaseException] = None
    while True:
        attempt += 1
        try:
            resp = _SESSION.post(
                STRATZ_GRAPHQL_URL,
                headers=headers,
                json={"query": query, "variables": variables},
                timeout=timeout,
            )
            # Do not retry 429, signal immediately
            if resp.status_code == 429:
                print("🛑 Stratz API returned 429 Too Many Requests")
                return resp
            # Retry on 5xx (except 509/over-quota variants would still not be 429, but rare)
            if 500 <= resp.status_code < 600 and attempt <= max_retries + 1:
                wait = 0.4 * attempt  # tiny linear backoff
                print(f"⏳ Stratz {resp.status_code} on attempt {attempt}, retrying in {wait:.1f}s…")
                time.sleep(wait)
                continue
            return resp
        except (Timeout, RequestsConnectionError) as e:
            last_exc = e
            if attempt <= max_retries + 1:
                wait = 0.4 * attempt
                print(f"⏳ Network issue on attempt {attempt}: {e}. Retrying in {wait:.1f}s…")
                time.sleep(wait)
                continue
            print(f"❌ Network failure after retries: {e}")
            return None
        except Exception as e:
            # Non-transient error (e.g., bad SSL, invalid URL) — don't retry blindly
            print(f"❌ Request error: {e}")
            return None


# --- Shared Stratz query runner ---
def post_stratz_query(query: str, variables: dict, token: str, timeout: int = 10) -> dict | str | None:
    """
    Low-level GraphQL runner with:
      • throttle() before each call
      • single-session reuse
      • 1 retry for transient failures (timeouts/5xx)
      • explicit quota sentinel ("quota_exceeded")
      • logs GraphQL errors array when present

    Return contract (unchanged):
      - dict: GraphQL data payload (data)
      - "quota_exceeded": quota signal
      - None: other failures
    """
    if not token:
        print("❌ Missing Stratz token (TOKEN env).")
        return None

    headers = {
        "User-Agent": "GuildBot/3.6 (+Stratz)",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        # Requests sets Connection: keep-alive by default for Session
    }

    throttle()  # ✅ Rate-limit per second/minute/hour caps

    resp = _request_with_retry(
        query=query,
        variables=variables,
        headers=headers,
        timeout=timeout,
        max_retries=1,  # one retry only for safety
    )

    if resp is None:
        return None

    if resp.status_code == 429:
        return "quota_exceeded"

    try:
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        if _is_quota_exceeded(resp, e):
            return "quota_exceeded"
        print(f"❌ Stratz HTTP/JSON failure: {e}")
        return None

    # Surface GraphQL errors (but still try to return data if present)
    if isinstance(payload, dict):
        _log_graphql_errors(payload)
        data = payload.get("data")
        return data

    print("❌ Unexpected response payload (not a JSON object).")
    return None


# --- Minimal match summary: for checking most recent match ID ---
def fetch_latest_match(steam_id: int, token: str) -> dict | None:
    """
    Fetch the most recent match ID for a given Steam32 ID.
    Used for polling latest match played.

    Returns:
      {"match_id": <int>} on success,
      {"error": "quota_exceeded"} on quota,
      None on other failures / not found.
    """
    query = """
    query ($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: { take: 1 }) {
          id
        }
      }
    }
    """
    variables = {"steamId": steam_id}
    data = post_stratz_query(query, variables, token)

    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}

    if not data or "player" not in data or not data["player"] or not data["player"].get("matches"):
        return None

    try:
        return {"match_id": data["player"]["matches"][0]["id"]}
    except Exception:
        return None


# --- Full match payload including extended stats and timeline ---
def fetch_full_match(steam_id: int, match_id: int, token: str) -> dict | None:
    """
    Full match data query with extended player + stat info (v4-ready).

    Returns:
      match object (dict) on success,
      {"error": "quota_exceeded"} on quota,
      None on other failures.
    """
    query = """
    query ($matchId: Long!) {
      match(id: $matchId) {
        id
        durationSeconds
        gameMode
        startDateTime
        players {
          steamAccountId
          isVictory
          isRadiant
          lane
          role
          roleBasic
          position
          partyId
          behavior
          intentionalFeeding
          kills
          deaths
          assists
          imp
          gold
          goldSpent
          networth
          goldPerMinute
          experiencePerMinute
          level
          item0Id
          item1Id
          item2Id
          item3Id
          item4Id
          item5Id
          backpack0Id
          backpack1Id
          backpack2Id
          neutral0Id
          hero {
            id
            name
            displayName
          }
          stats {
            campStack
            networthPerMinute
            experiencePerMinute
            actionsPerMinute
            heroDamagePerMinute
            towerDamagePerMinute
            killEvents { time target }
            deathEvents { time }
            assistEvents { time target }
            wards { time }
            wardDestruction { time }
            courierKills { time }
            runes { time }
          }
        }
      }
    }
    """
    variables = {"matchId": match_id}
    data = post_stratz_query(query, variables, token, timeout=15)

    if data == "quota_exceeded":
        return {"error": "quota_exceeded"}

    if not data:
        return None

    if os.getenv("DEBUG_MODE") == "1":
        print("🔎 Full match response:")
        try:
            print(json.dumps(data, indent=2))
        except Exception:
            print(str(data))

    return data.get("match")
