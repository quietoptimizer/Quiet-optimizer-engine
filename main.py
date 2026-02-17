import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

SYSTEM_STYLE = """
You are "The Quiet Optimizer" — anonymous, calm, strategic.
Short lines. High signal. No fluff.
Pillars: anime, gaming, psychology, strategy.
"""

def send_message(chat_id: int, text: str):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def openai_generate(prompt: str) -> str:
    r = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-5.2",
            "input": [
                {"role": "system", "content": SYSTEM_STYLE},
                {"role": "user", "content": prompt},
            ],
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
