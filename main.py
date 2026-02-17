import os
import time
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# Required env vars in Render:
# TELEGRAM_BOT_TOKEN = 1234567890:ABCDEF....
# (OPENAI_API_KEY optional if you have billing)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Simple per-chat throttle to avoid spam
LAST_MESSAGE_AT = {}
MIN_SECONDS_BETWEEN_MESSAGES = 2

TEMPLATES = {
    "anime": [
        "Quiet power: train one small skill today. No audience needed.",
        "Your rival is yesterday's you. Beat them quietly.",
        "If the arc feels slow, good. That is the training montage."
    ],
    "gaming": [
        "Optimize daily. Small upgrades matter.",
        "Meta changes. Fundamentals stay.",
        "Stay calm. Make clean decisions."
    ],
    "psychology": [
        "Name the emotion, then choose the action. Feeling is not fate.",
        "Confidence grows from repetition. Stack small wins.",
        "Protect your attention. It is your real currency."
    ],
    "strategy": [
        "Clarify the objective. Remove everything that does not serve it.",
        "Good strategy is subtraction: fewer moves, sharper impact.",
        "Win quietly: prepare more than you announce."
    ],
    "help": [
        "Commands:\n"
        "/anime\n"
        "/gaming\n"
        "/psychology\n"
        "/strategy\n"
        "/help\n"
        "/mode"
    ]
}

def telegram_api_url(method):
    return "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/" + method

def send_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is missing or empty")
        return

    url = telegram_api_url("sendMessage")
    payload = {"chat_id": chat_id, "text": text}

    try:
        r = requests.post(url, json=payload, timeout=20)
        print("sendMessage status:", r.status_code)
        print("sendMessage body:", r.text[:300])
    except Exception as e:
        print("sendMessage exception:", repr(e))

def pick(pillar):
    return random.choice(TEMPLATES.get(pillar, ["No templates available."]))

def build_reply(text):
    t = (text or "").strip().lower()

    if t == "/start" or t.startswith("/help"):
        return pick("help")

    if t.startswith("/mode"):
        if TELEGRAM_BOT_TOKEN:
            return "Mode: template-only (OpenAI not required)."
        return "Mode: missing TELEGRAM_BOT_TOKEN."

    if t.startswith("/anime"):
        return pick("anime")

    if t.startswith("/gaming"):
        return pick("gaming")

    if t.startswith("/psychology"):
        return pick("psychology")

    if t.startswith("/strategy"):
        return pick("strategy")

    return "Use /anime /gaming /psychology /strategy or /help."

@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Quiet Optimizer Online", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    # Always return 200 to Telegram, even if something goes wrong.
    try:
        update = request.get_json(silent=True) or {}

        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = message.get("text") or ""

        print("incoming chat_id:", chat_id)
        print("incoming text:", repr(text)[:200])

        if not chat_id:
            return "OK", 200

        # throttle
        now = int(time.time())
        last = LAST_MESSAGE_AT.get(chat_id, 0)
        if now - last < MIN_SECONDS_BETWEEN_MESSAGES:
            return "OK", 200
        LAST_MESSAGE_AT[chat_id] = now

        reply = build_reply(text)
        send_message(chat_id, reply)

    except Exception as e:
        print("webhook exception:", repr(e))

    return "OK", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
