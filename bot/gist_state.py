import os
import json
import requests

GIST_ID = os.getenv("GIST_ID")
GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_FILENAME = "state.json"

HEADERS = {
    "Authorization": f"Bearer {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def load_state():
    """
    Loads a set of known match IDs from the GitHub Gist (state.json).
    Returns: set of match ID strings.
    """
    if not GIST_ID or not GIST_TOKEN:
        print("❌ Missing GIST_ID or GIST_TOKEN environment variables.")
        return set()

    try:
        response = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS)
        response.raise_for_status()
        content = response.json()["files"][GIST_FILENAME]["content"]
        match_ids = json.loads(content)
        return set(match_ids)
    except Exception as e:
        print(f"⚠️ Failed to load state.json: {e}")
        return set()

def save_state(match_id_set):
    """
    Saves the set of known match IDs to the GitHub Gist as state.json.
    Args:
        match_id_set: set of match ID strings
    """
    if not GIST_ID or not GIST_TOKEN:
        print("❌ Missing GIST_ID or GIST_TOKEN environment variables.")
        return

    try:
        payload = {
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(list(match_id_set), indent=2)
                }
            }
        }
        response = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()
        print("📝 Updated state.json on GitHub Gist")
    except Exception as e:
        print(f"❌ Failed to update state.json: {e}")

# ✅ Add alias for backward compatibility
update_state = save_state
