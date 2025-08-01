# server.py

from flask import Flask
from multiprocessing import Process
import fcntl
import os
from bot.runner import run_bot

app = Flask(__name__)

LOCK_FILE = "/tmp/guildbot.lock"

def safe_run_bot():
    try:
        with open(LOCK_FILE, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print("🔐 Acquired lock. Running GuildBot.")
            run_bot()
            print("✅ Bot finished. Releasing lock.")
    except BlockingIOError:
        print("🛑 GuildBot is already running. Skipping.")
        return

@app.route("/")
def index():
    return "✅ GuildBot Flask server is running. Try /run to trigger a full match check."

@app.route("/run")
def run():
    try:
        Process(target=safe_run_bot).start()
        return "✅ GuildBot run triggered. Check logs for progress."
    except Exception as e:
        return f"❌ Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
