import os
import requests
from flask import Flask, request
import os, requests

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json(silent=True) or {}
        print("Incoming update:", update) # shows what Telegram sent

        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = (message.get("text") or "").strip()

        # If Telegram sends something that isn't a message, don't crash
        if not chat_id or not text:
            return "OK", 200

        # simple command routing
        if text.lower().startswith("/anime"):
            reply = openai_generate("Give me 3 short anime-themed posts for The Quiet Optimizer.")
        else:
            reply = openai_generate(f"Reply briefly in the tone of The Quiet Optimizer to: {text}")

        send_telegram(chat_id, reply)

    except Exception as e:
        print("Webhook error:", repr(e)) # IMPORTANT: shows the actual crash in logs

    # Always return 200 so Telegram stops retrying
    return "OK", 200

def send_telegram(chat_id: int, text: str):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=20)
    print("Telegram send status:", r.status_code, r.text[:200])
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()

    output_text = ""
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                output_text += content.get("text", "")

    return output_text.strip()

@app.route("/")
def home():
    return "Quiet Optimizer Online"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    message = update.get("message")

    if not message:
        return "ok", 200

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/anime"):
        response = openai_generate("Generate 3 short posts using anime as a lens for psychology and strategy.")
    elif text.startswith("/gaming"):
        response = openai_generate("Generate 3 short posts about gaming strategy that applies to real life.")
    elif text.startswith("/psy"):
        response = openai_generate("Generate 3 short posts about psychology and identity growth.")
    elif text.startswith("/strat"):
        response = openai_generate("Generate 3 short posts about strategy and long-term thinking.")
    else:
        response = openai_generate(text)

    send_message(chat_id, response)
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
