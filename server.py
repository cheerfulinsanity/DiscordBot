from flask import Flask
import requests
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to test the Stratz fetch."

@app.route("/run")
def run():
    token = os.getenv("TOKEN")
    steam_id = 84228471  # hardcoded test player

    query = """
    query GetLatestMatch($steamId: Long!) {
      player(steamAccountId: $steamId) {
        matches(request: { take: 1 }) {
          id
          durationSeconds
          players {
            steamAccountId
            isVictory
            hero {
              id
              name
            }
            kills
            deaths
            assists
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
        "variables": { "steamId": steam_id }
    }

    try:
        res = requests.post("https://api.stratz.com/graphql", headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        match = data["data"]["player"]["matches"][0]

        player = next(p for p in match["players"] if p["steamAccountId"] == steam_id)

        result = {
            "match_id": match["id"],
            "hero_name": player["hero"]["name"],
            "kills": player["kills"],
            "deaths": player["deaths"],
            "assists": player["assists"],
            "won": player["isVictory"]
        }

        return f"🧙 {result['hero_name']}: {result['kills']}/{result['deaths']}/{result['assists']} — {'🏆 Win' if result['won'] else '💀 Loss'} (Match ID: {result['match_id']})"

    except Exception as e:
        return f"❌ Error: {str(e)}\nRaw response: {res.text}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
