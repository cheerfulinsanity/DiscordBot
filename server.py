# server.py

from flask import Flask
from bot.runner import run_bot

app = Flask(__name__)

@app.route("/")
def index():
    return "GuildBot is running."

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
