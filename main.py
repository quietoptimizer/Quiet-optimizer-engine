import os
import time
import random
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = "gpt-4o-mini"

LAST_MESSAGE_AT = {}
MIN_SECONDS_BETWEEN_MESSAGES = 3

TEMPLATES = {
    "anime": [
        "Train quietly. Win loudly.",
        "Your rival is yesterday's you.",
        "Discipline beats talent when talent is lazy."
    ],
    "gaming": [
        "Optimize daily. Small upgrades matter.",
        "Meta changes. Fundamentals stay.",
        "Stay calm. Make clean decisions."
    ],
    "psychology": [
        "Name the emotion. Choose the action.",
        "Confidence grows from repetition.",
        "Protect your attention."
    ],
    "strategy": [
        "Clarity before action.",
        "Remove what does not serve the goal.",
        "Consistency wins."
    ]
}

def telegram_url(method):
    return "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/" + method

def send_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    requests.post(telegram_url("sendMessage"), json={
        "chat_id": chat_id,
        "text": text
    })

def handle_text(text):
    text = text.lower()

    if text.startswith("/anime"):
        return random.choice(TEMPLATES["anime"])

    if text.startswith("/gaming"):
        return random.choice(TEMPLATES["gaming"])

    if text.startswith("/psychology"):
        return random.choice(TEMPLATES["psychology"])

    if text.startswith("/strategy"):
        return random.choice(TEMPLATES["strategy"])

    if text.startswith("/mode"):
        if OPENAI_API_KEY:
            return "AI mode enabled"
        return "Template mode"

    return "Use /anime /gaming /psychology /strategy"

@app.route("/", methods=["GET"])
def home():
    return "Quiet Optimizer Online", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json() or {}
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id:
            return "OK", 200

        now = int(time.time())
        last = LAST_MESSAGE_AT.get(chat_id, 0)
        if now - last < MIN_SECONDS_BETWEEN_MESSAGES:
            return "OK", 200
        LAST_MESSAGE_AT[chat_id] = now

        reply = handle_text(text)
        send_message(chat_id, reply)

    except Exception as e:
        print("Error:", e)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
