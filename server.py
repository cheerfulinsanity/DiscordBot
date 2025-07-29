from flask import Flask
import main  # your refactored bot logic

app = Flask(__name__)

@app.route("/")
def home():
    return "GuildBot is running."

@app.route("/run")
def trigger():
    try:
        main.run_bot()
        return "Bot ran successfully!"
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
