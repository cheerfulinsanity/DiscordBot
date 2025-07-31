# server.py

from flask import Flask
import os
from bot.runner import run_bot

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to test the full player loop."

@app.route("/run")
def run():
    try:
        lines = run_bot()
        return "<br>".join(lines)
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
