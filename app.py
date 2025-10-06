from flask import Flask, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)

# Read FORM_URL and USERNAME from environment variables
FORM_URL = os.environ.get("FORM_URL")
USERNAME = os.environ.get("USERNAME")
FIELD_ID = "entry.1271071818"  # update if your Google Form uses another field ID

# Telegram Bot settings (set these in Render environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not FORM_URL or not USERNAME:
    raise ValueError("FORM_URL and USERNAME environment variables must be set!")


def send_telegram(message: str):
    """Send a log message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured, skipping message:", message)
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        print("⚠️ Failed to send Telegram message:", e)


# Submission interval (seconds)
SUBMIT_INTERVAL = 3* 0 * 60  # every 6 hours


def submit_form():
    """Submits the Google Form"""
    try:
        data = {FIELD_ID: USERNAME}
        response = requests.post(FORM_URL, data=data)
        if response.ok:
            msg = "✅ Form submitted successfully"
            print(msg)
            send_telegram(msg)
        else:
            msg = f"❌ Failed to submit, status: {response.status_code}"
            print(msg)
            send_telegram(msg)
    except Exception as e:
        msg = f"❌ Error submitting form: {e}"
        print(msg)
        send_telegram(msg)


def periodic_submit():
    """Runs form submission periodically in background"""
    while True:
        submit_form()
        time.sleep(SUBMIT_INTERVAL)


def keep_alive():
    """Keeps service alive by pinging itself every 10 minutes"""
    while True:
        try:
            requests.get(SERVICE_URL)
            msg = "Pinged self to stay alive ✅"
            print(msg)
            send_telegram(msg)
        except Exception as e:
            msg = f"Failed to ping self: {e}"
            print(msg)
            send_telegram(msg)
        time.sleep(10 * 60)  # every 10 minutes


@app.route("/")
def home():
    return "🟢 Service is running!"


@app.route("/submit")
def submit_endpoint():
    """Endpoint to manually trigger form submission"""
    submit_form()
    return jsonify({"status": "submitted"})


if __name__ == "__main__":
    # Set your Render service URL after deployment
    SERVICE_URL = "https://your-render-service.onrender.com"

    # Start background threads
    threading.Thread(target=periodic_submit, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    # Use Render-assigned PORT if available
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
