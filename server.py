# server.py

from flask import Flask
from threading import Thread, Lock
from bot.runner import run_bot

app = Flask(__name__)

run_lock = Lock()

def safe_run_bot():
    if run_lock.locked():
        print("🛑 GuildBot is already running. Skipping.")
        return
    with run_lock:
        print("🔐 Running GuildBot.")
        run_bot()
        print("✅ GuildBot complete.")

@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to trigger a full match check."

@app.route("/run")
def run():
    try:
        Thread(target=safe_run_bot).start()
        return "✅ GuildBot run triggered. Check logs for progress."
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
