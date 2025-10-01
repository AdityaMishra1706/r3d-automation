from flask import Flask, jsonify, request
import requests
import threading
import time
import os

app = Flask(__name__)

# Read FORM_URL and USERNAME from environment variables
FORM_URL = os.environ.get("FORM_URL")
USERNAME = os.environ.get("USERNAME")
FIELD_ID = "entry.1271071818"  # Google Form field ID

if not FORM_URL or not USERNAME:
    raise ValueError("FORM_URL and USERNAME environment variables must be set!")

# Submission interval (seconds)
SUBMIT_INTERVAL = 6 * 60 * 60  # 6 hours

# Global variable for the service URL
SERVICE_URL = None

def submit_form():
    """Submits the Google Form"""
    try:
        data = {FIELD_ID: USERNAME}
        response = requests.post(FORM_URL, data=data)
        if response.ok:
            print("✅ Form submitted successfully")
        else:
            print("❌ Failed to submit, status:", response.status_code)
    except Exception as e:
        print("❌ Error submitting form:", e)

def periodic_submit():
    """Runs form submission every 6 hours"""
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
                print("Pinged self to stay alive ✅")
            except Exception as e:
                print("Failed to ping self:", e)
        time.sleep(10 * 60)  # every 10 minutes

@app.before_first_request
def detect_service_url():
    """Detect SERVICE_URL dynamically from the first request"""
    global SERVICE_URL
    if not SERVICE_URL:
        # Use the Host header to build the full URL
        host = request.host_url.rstrip("/")
        SERVICE_URL = host
        print(f"Detected SERVICE_URL: {SERVICE_URL}")

@app.route("/")
def home():
    return "🟢 Service is running!"

@app.route("/submit")
def submit_endpoint():
    submit_form()
    return jsonify({"status": "submitted"})

if __name__ == "__main__":
    threading.Thread(target=periodic_submit, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
