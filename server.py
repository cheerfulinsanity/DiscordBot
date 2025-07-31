from flask import Flask
import os
from bot.stratz import fetch_latest_match

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to test the Stratz fetch."

@app.route("/run")
def run():
    try:
        token = os.getenv("TOKEN")
        steam_id = 84228471

        match = fetch_latest_match(steam_id, token)

        return (
            f"🧙 {match['hero_name']}: {match['kills']}/"
            f"{match['deaths']}/{match['assists']} — "
            f"{'🏆 Win' if match['won'] else '💀 Loss'} "
            f"(Match ID: {match['match_id']})"
        )

    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
