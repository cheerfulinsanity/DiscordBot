# bot/gist_state.py

import os
import json
import requests

GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"
GIST_HEADERS = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def load_state():
    try:
        r = requests.get(GIST_API_URL, headers=GIST_HEADERS)
        if r.status_code == 200:
            files = r.json().get("files", {})
            state_content = files.get("state.json", {}).get("content", "{}")
            return json.loads(state_content)
        else:
            print("⚠️ Could not load state.json from Gist:", r.text)
    except Exception as e:
        print("⚠️ Exception loading state.json from Gist:", e)
    return {}

def save_state(state):
    payload = {
        "files": {
            "state.json": {
                "content": json.dumps(state, indent=2)
            }
        }
    }
    try:
        r = requests.patch(GIST_API_URL, headers=GIST_HEADERS, json=payload)
        if r.status_code != 200:
            print("⚠️ Failed to update Gist state:", r.text)
    except Exception as e:
        print("⚠️ Exception saving state.json to Gist:", e)
