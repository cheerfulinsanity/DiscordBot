# server.py

from flask import Flask
import threading
from bot.runner import run_bot

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to trigger a full match check."

@app.route("/run")
def run():
    try:
        threading.Thread(target=run_bot).start()
        return "✅ GuildBot run triggered. Check Render logs for progress."
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
