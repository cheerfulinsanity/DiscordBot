# bot/gist_state.py

import requests
import os
import json

GIST_ID = "2a6cdb57dcdbd69d7468f612a31691f9"
GIST_FILENAME = "state.json"
GITHUB_TOKEN = os.getenv("GIST_TOKEN")

def load_state():
    """Fetches the current state.json from GitHub Gist"""
    res = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    })
    res.raise_for_status()
    content = res.json()["files"][GIST_FILENAME]["content"]
    return json.loads(content)

def save_state(new_state):
    """Updates state.json in GitHub Gist with the provided dictionary"""
    payload = {
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(new_state, indent=2)
            }
        }
    }
    res = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }, json=payload)
    res.raise_for_status()
    return True
