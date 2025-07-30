# server.py

from flask import Flask
from bot.runner import run_bot

app = Flask(__name__)

@app.route("/")
def index():
    return "GuildBot is running!"

@app.route("/run")
def trigger():
    print("🟢 /run endpoint triggered")
    try:
        run_bot()
        print("✅ run_bot() finished without crashing")
        return "Bot ran successfully!"
    except Exception as e:
        print(f"❌ Exception inside run_bot(): {e}")
        return f"Error: {str(e)}", 500
