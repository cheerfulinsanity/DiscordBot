import os
import requests

# Load from environment
GIST_TOKEN = os.getenv("GIST_TOKEN")
GIST_ID = os.getenv("GIST_ID")

print("🧪 ENVIRONMENT CHECK")
print("GIST_TOKEN loaded:", bool(GIST_TOKEN))
print("GIST_ID loaded:", GIST_ID[:8] + "..." if GIST_ID else "Missing")
print("")

if not GIST_TOKEN or not GIST_ID:
    print("❌ Missing GIST_TOKEN or GIST_ID. Exiting early.")
    exit(1)

# Try to fetch the Gist
print("🔍 FETCHING GIST")
headers = {
    "Authorization": f"token {GIST_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
url = f"https://api.github.com/gists/{GIST_ID}"
print("Request URL:", url)
res = requests.get(url, headers=headers)

print("Status code:", res.status_code)
print("Response:")
print(res.text)

if res.status_code == 200:
    print("\n✅ SUCCESS — Gist was accessed correctly.")
elif res.status_code == 401:
    print("\n❌ 401 Unauthorized — token was invalid or not recognized.")
elif res.status_code == 404:
    print("\n❌ 404 Not Found — Gist ID is invalid or not visible to token.")
else:
    print("\n⚠️ Unexpected response.")
