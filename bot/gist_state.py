import os
import json
import requests

GIST_ID = os.getenv("GIST_ID")
GIST_TOKEN = os.getenv("GIST_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

FILENAME = "state.json"

def load_state():
    """
    Fetches state.json from the GitHub Gist and returns its contents as a dict.
    If the Gist is missing or corrupt, returns an empty dict.
    """
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        files = response.json().get("files", {})
        if FILENAME in files and files[FILENAME]["content"]:
            return json.loads(files[FILENAME]["content"])
    except Exception as e:
        print(f"⚠️ Failed to load state.json: {e}")
    return {}

def save_state(state):
    """
    Updates the state.json file in the GitHub Gist with the given dict.
    """
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        payload = {
            "files": {
                FILENAME: {
                    "content": json.dumps(state, indent=2)
                }
            }
        }
        response = requests.patch(url, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()
        print("📝 Updated state.json on GitHub Gist")
    except Exception as e:
        print(f"❌ Failed to update state.json: {e}")
