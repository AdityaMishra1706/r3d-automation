from flask import Flask, jsonify, request
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

# Global service URL (detected at runtime)
SERVICE_URL = None


def send_telegram_message(text):
    """Send a message to Telegram if bot credentials are set"""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
            requests.post(url, data=payload, timeout=10)
        except Exception as e:
            print("⚠️ Failed to send Telegram message:", e)


def submit_form():
    """Submits the Google Form"""
    try:
        data = {FIELD_ID: USERNAME}
        response = requests.post(FORM_URL, data=data, timeout=10)
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
                requests.get(SERVICE_URL, timeout=10)
                msg = "Pinged self to stay alive ✅"
                print(msg)
                send_telegram_message(msg)
            except Exception as e:
                msg = f"Failed to ping self: {e}"
                print(msg)
                send_telegram_message(msg)
        time.sleep(10 * 60)


@app.before_first_request
def detect_service_url():
    """Detect SERVICE_URL dynamically from first incoming request"""
    global SERVICE_URL
    if not SERVICE_URL:
        SERVICE_URL = request.host_url.rstrip("/")
        print(f"🔍 Detected SERVICE_URL: {SERVICE_URL}")
        send_telegram_message(f"🔍 Detected SERVICE_URL: {SERVICE_URL}")


@app.route("/")
def home():
    return "🟢 Service is running!"


@app.route("/submit")
def submit_endpoint():
    """Endpoint to manually trigger form submission"""
    submit_form()
    return jsonify({"status": "submitted"})


if __name__ == "__main__":
    # Start background threads
    threading.Thread(target=periodic_submit, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    # Use Render-assigned PORT if available
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
