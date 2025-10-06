from flask import Flask, jsonify
import requests
import threading
import time
from bs4 import BeautifulSoup   # <-- NEW
import re  # <-- NEW: For regex-based extraction of dynamic code

app = Flask(__name__)

# Google Form formResponse URL
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLScM4xmi39q-gxy6CbafHBeSXGGuIk82EWqxmtlnhwBYWMHkTw/formResponse"
FORM_VIEW_URL = FORM_URL.replace("/formResponse", "/viewform")

# Google Form field entry IDs
FIELD_IDS = [
    "entry.2147445338",  # Field 1: category
    "entry.1178506819",  # Field 2: language
    "entry.1696186446",  # Field 3: joke type
    "entry.1624379107",  # Field 4: joke setup or text
    "entry.1434885666",  # Field 5: joke delivery or empty
    "entry.74418499"     # Field 6: dynamic code (changes!)
]

# Telegram bot config
TELEGRAM_BOT_TOKEN = "xxxx"
TELEGRAM_CHAT_ID = "xxxx"

# Submit interval (60 sec)
SUBMIT_INTERVAL = 60
SERVICE_URL = None

JOKE_API_URL = "https://v2.jokeapi.dev/joke/Any"


def send_telegram(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        except Exception as e:
            print("❌ Telegram error:", e)


def fetch_dynamic_code():
    """Fetch the dynamic code from the Google Form view page by searching the entire HTML"""
    try:
        res = requests.get(FORM_VIEW_URL)
        res.raise_for_status()
        
        # Search the entire HTML text for the pattern "Type this code: <code>"
        # Assuming the code is uppercase alphanumeric (e.g., L6TD4)
        match = re.search(r'Type this code:\s*([A-Z0-9]+)', res.text)
        if match:
            code = match.group(1).strip()
            print(f"✅ Found dynamic code: {code}")
            return code
        
        print("⚠️ No dynamic code pattern found in HTML")
        return None
    except Exception as e:
        print("❌ Failed to fetch dynamic code:", e)
        return None


def fetch_joke_data():
    try:
        response = requests.get(JOKE_API_URL)
        response.raise_for_status()
        data = response.json()

        category = data.get("category", "Unknown")
        lang = data.get("lang", "en")
        joke_type = data.get("type", "single")

        if joke_type == "single":
            setup = data.get("joke", "")
            delivery = ""
        elif joke_type == "twopart":
            setup = data.get("setup", "")
            delivery = data.get("delivery", "")
        else:
            setup = ""
            delivery = ""

        # ✅ Fetch dynamic code instead of fixed value
        dynamic_code = fetch_dynamic_code()
        if not dynamic_code:
            print("⚠️ No dynamic code found, skipping submit")
            return None, None, None

        values = [
            category,
            lang,
            joke_type,
            setup,
            delivery,
            dynamic_code   # <-- now dynamic
        ]

        return values, setup, delivery

    except Exception as e:
        print(f"Failed to fetch joke data: {e}")
        return None, None, None


def submit_form(dynamic_values=None, setup="", delivery=""):
    try:
        if dynamic_values:
            data = {field: value for field, value in zip(FIELD_IDS, dynamic_values)}
        else:
            print("No values provided for submission")
            return

        response = requests.post(FORM_URL, data=data)
        if response.ok:
            msg = "✅ Form submitted successfully."
            print(msg)
            send_telegram(msg)

            joke_message = f"🃏 Joke:\n{setup}"
            if delivery:
                joke_message += f"\n{delivery}"
            send_telegram(joke_message)
        else:
            msg = f"❌ Form submission failed. Status code: {response.status_code}"
            print(msg)
            send_telegram(msg)

    except Exception as e:
        msg = f"❌ Error submitting form: {e}"
        print(msg)
        send_telegram(msg)


def periodic_submit():
    while True:
        values, setup, delivery = fetch_joke_data()
        if values:
            submit_form(dynamic_values=values, setup=setup, delivery=delivery)
        else:
            print("Skipping submit due to fetch error.")
        time.sleep(SUBMIT_INTERVAL)


def keep_alive():
    while True:
        if SERVICE_URL:
            try:
                requests.get(SERVICE_URL)
                print("🔄 Pinged self to stay alive.")
            except Exception as e:
                print(f"❌ Keep-alive ping failed: {e}")
        time.sleep(10 * 60)


@app.route("/")
def home():
    return "🟢 Service is running!"


@app.route("/submit")
def submit_now():
    values, setup, delivery = fetch_joke_data()
    if values:
        submit_form(dynamic_values=values, setup=setup, delivery=delivery)
        return jsonify({"status": "submitted", "data": values})
    else:
        return jsonify({"status": "failed", "error": "Could not fetch joke data"}), 500


if __name__ == "__main__":
    threading.Thread(target=periodic_submit, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
