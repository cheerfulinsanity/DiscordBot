# server.py
from flask import Flask
import requests
import os

app = Flask(__name__)

@app.route("/run", methods=["GET"])
def run():
    token = os.getenv("TOKEN")
    steam_id = 84228471  # hardcoded test player

    query = """
    query GetLatestMatch($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: {take: 1}) {
          id
          durationSeconds
          players {
            steamAccountId
            hero { name }
            isVictory
            killCount
            deathCount
            assistCount
          }
        }
      }
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "STRATZ_API"
    }

    payload = {
        "query": query,
        "variables": {"steamId": steam_id}
    }

    try:
        res = requests.post("https://api.stratz.com/graphql", headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        match = data["data"]["player"]["matches"][0]
        player = next(p for p in match["players"] if p["steamAccountId"] == steam_id)

        hero = player["hero"]["name"]
        k, d, a = player["killCount"], player["deathCount"], player["assistCount"]
        win = "🏆 Win" if player["isVictory"] else "💀 Loss"

        return f"🧙 {hero}: {k}/{d}/{a} — {win} (Match ID: {match['id']})"

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    app.run()
