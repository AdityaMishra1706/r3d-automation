import requests
import os
import time
import threading
from flask import Flask, jsonify

app = Flask(__name__)

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7yF9ShyFm9Q0UXMsqVToz27hX87tngstGMGjgBES_mZCqWA/formResponse"

# Google Form field IDs
FIELD_GAY = "entry.849642921"
FIELD_JOKE = "entry.1430686465"

# Default multiple choice option (must match exactly with form option text)
CHOICE_VALUE = os.environ.get("CHOICE_VALUE", "Haan")

# Interval for submitting (seconds)
SUBMIT_INTERVAL = 5  # every 6 hours


def get_joke():
    """Fetch a random joke from JokeAPI"""
    try:
        resp = requests.get(
            "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
        )
        data = resp.json()
        if data.get("type") == "single":
            return data.get("joke", "No joke found")
        elif data.get("type") == "twopart":
            return f"{data.get('setup')} - {data.get('delivery')}"
        else:
            return "No joke found"
    except Exception as e:
        return f"Error fetching joke: {e}"


def submit_form():
    """Submits the Google Form with a joke and choice"""
    try:
        joke = get_joke()
        data = {
            FIELD_JOKE: joke,
            FIELD_GAY: CHOICE_VALUE
        }
        response = requests.post(FORM_URL, data=data)
        if response.ok:
            print("✅ Submitted form successfully with joke:", joke)
        else:
            print("❌ Failed to submit form, status:", response.status_code)
    except Exception as e:
        print("❌ Error submitting form:", e)


def periodic_submit():
    """Runs form submission periodically"""
    while True:
        submit_form()
        time.sleep(SUBMIT_INTERVAL)


@app.route("/")
def home():
    return "🟢 Joke Form Submitter is running!"


@app.route("/submit")
def manual_submit():
    submit_form()
    return jsonify({"status": "submitted"})


if __name__ == "__main__":
    # Start background thread
    threading.Thread(target=periodic_submit, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
