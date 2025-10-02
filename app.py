from flask import Flask, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)

# Google Form settings from environment variables
FORM_URL = os.environ.get("FORM_URL")
USERNAME = os.environ.get("USERNAME")
FIELD_ID = "entry.1271071818"

if not FORM_URL or not USERNAME:
    raise ValueError("FORM_URL and USERNAME environment variables must be set!")

# Telegram bot credentials from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Submission interval (seconds)
SUBMIT_INTERVAL = 6 * 60 * 60  # 6 hours

# Declare SERVICE_URL globally
SERVICE_URL = None


def send_telegram_message(text):
    """Send a message to Telegram if bot credentials are set"""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
            requests.post(url, data=payload)
        except Exception as e:
            print("⚠️ Failed to send Telegram message:", e)


def submit_form():
    """Submits the Google Form"""
    try:
        data = {FIELD_ID: USERNAME}
        response = requests.post(FORM_URL, data=data)
        if response.ok:
            msg = "✅ Form submitted successfully"
            print(msg)
            send_telegram_message(msg)
        else:
            msg = f"❌ Failed to submit, status: {response.status_code}"
            print(msg)
            send_telegram_message(msg)
    except Exception as e:
        msg = f"❌ Error submitting form: {e}"
        print(msg)
        send_telegram_message(msg)


def periodic_submit():
    """Runs form submission periodically in background"""
    while True:
        submit_form()
        time.sleep(SUBMIT_INTERVAL)


def keep_alive():
    """Keeps service alive by pinging itself every 10 minutes"""
    global SERVICE_URL
    while True:
        if SERVICE_URL:
            try:
                requests.get(SERVICE_URL)
                msg = "Pinged self to stay alive ✅"
                print(msg)
                send_telegram_message(msg)
            except Exception as e:
                msg = f"Failed to ping self: {e}"
                print(msg)
                send_telegram_message(msg)
        time.sleep(10 * 60)


@app.route("/")
def home():
    return "🟢 Service is running!"


@app.route("/submit")
def submit_endpoint():
    """Endpoint to manually trigger form submission"""
    submit_form()
    return jsonify({"status": "submitted"})


if __name__ == "__main__":
    # Set SERVICE_URL manually after deployment
    SERVICE_URL = "https://your-render-service.onrender.com"

    # Start background threads
    threading.Thread(target=periodic_submit, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    # Use Render-assigned PORT if available
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
