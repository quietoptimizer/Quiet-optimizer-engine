
# main.py
# Quiet Optimizer (Render + Telegram Webhook) — resilient, phone-friendly, no-crash
# - Always returns 200 OK to Telegram (prevents retry storms)
# - Works with/without OPENAI_API_KEY (falls back to templates)
# - Handles OpenAI 429 rate limits gracefully (no 500)
# - Simple command routing: /anime /gaming /psychology /strategy /help

import os
import time
import random
import requests
from flask import Flask, request

app = Flask(__name__)

# -----------------------------
# Config
# -----------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Optional: set a model you have access to. If you don’t have billing, OpenAI may 429.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# Simple in-memory rate limiter per chat (prevents spam + reduces 429)
# NOTE: resets on deploy/restart (fine for Render free tier).
LAST_MESSAGE_AT = {} # chat_id -> unix time (seconds)
MIN_SECONDS_BETWEEN_MESSAGES = int(os.getenv("MIN_SECONDS_BETWEEN_MESSAGES", "3"))

# -----------------------------
# Template Library (fallback mode)
# -----------------------------
TEMPLATES = {
    "anime": [
        "Quiet power: train one small skill today. No audience needed.",
        "Your rival is yesterday’s you. Beat them quietly.",
        "If the arc feels slow, good. That’s the training montage.",
        "Discipline is a superpower. Stack one rep. Stack one page.",
        "The boss fight is your habits. Grind in silence.",
    ],
    "gaming": [
        "Optimize your build: one weakness at a time. Patch notes daily.",
        "Play the long game: XP comes from consistency, not hype.",
        "Stop chasing loot. Upgrade your fundamentals: sleep, food, movement.",
        "Your meta is focus. Your combo is routine + repetition.",
        "Don’t tilt. Re-center. One clean decision at a time.",
    ],
    "psychology": [
        "Name the emotion, then choose the action. Feeling isn’t fate.",
        "Your brain learns what you repeat. Repeat the useful patterns.",
        "Small wins rewire confidence. Collect them daily.",
        "Protect your attention like it’s currency—because it is.",
        "Calm is a skill. Practice it like strength training.",
    ],
    "strategy": [
        "Clarify the objective. Remove everything that doesn’t serve it.",
        "Good strategy is subtraction: fewer moves, sharper impact.",
        "Win quietly: prepare more than you announce.",
        "Measure what matters weekly. Adjust without drama.",
        "If it’s not scheduled, it’s not real. Put it on the board.",
    ],
    "help": [
        "Commands:\n"
        "/anime — short anime-themed post\n"
        "/gaming — short gaming-themed post\n"
        "/psychology — mindset/behavior post\n"
        "/strategy — planning/decision post\n"
        "/mode — shows whether AI is enabled\n"
        "Send any message for a short reply.",
    ],
}

# -----------------------------
# Utility: Telegram
# -----------------------------
def telegram_api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

def send_telegram(chat_id: int, text: str) -> None:
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set.")
        return

    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(telegram_api_url("sendMessage"), json=payload, timeout=20)
        print("Telegram send status:", r.status_code, r.text[:200])
    except Exception as e:
        print("Telegram send exception:", repr(e))

# -----------------------------
# Utility: OpenAI (optional)
# -----------------------------
def openai_generate(prompt: str) -> str:
    """
    Uses the OpenAI Responses API if OPENAI_API_KEY is set.
    If unavailable / rate-limited / error, returns a friendly fallback.
    """
    if not OPENAI_API_KEY:
        return "AI is currently disabled. I’m running in template mode. Try /anime /gaming /psychology /strategy."

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "input": prompt,
    }

    try:
        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=30,
        )

        # Handle rate limit without crashing webhook
        if r.status_code == 429:
            print("OpenAI rate limited (429). Body:", r.text[:300])
            return "I’m rate-limited right now. Try again in 30–60 seconds."

        # Handle auth/other errors without raising exceptions
        if r.status_code >= 400:
            print("OpenAI error:", r.status_code, r.text[:300])
            return "AI is unavailable right now. Try again later."

        data = r.json()

        # Best-effort extraction for Responses API
        try:
            return data["output"][0]["content"][0]["text"].strip()
        except Exception:
            # If shape differs, return a safe fallback
            return "I’m online, but I hit a formatting snag. Try again."

    except Exception as e:
        print("OpenAI exception:", repr(e))
        return "AI is temporarily unavailable. Try again later."

# -----------------------------
# Command routing
# -----------------------------
def pick_template(pillar: str) -> str:
    items = TEMPLATES.get(pillar, [])
    if not items:
        return "No templates found."
    return random.choice(items)

def handle_text(text: str) -> str:
    t = (text or "").strip()
    low = t.lower()

    # Commands
    if low.startswith("/help") or low == "/start":
        return pick_template("help")

    if low.startswith("/mode"):
        if OPENAI_API_KEY:
            return f"Mode: AI enabled (model: {OPENAI_MODEL})."
        return "Mode: Template-only (AI disabled / no key)."

    if low.startswith("/anime"):
        # If AI is enabled, you can choose to generate; otherwise templates
        if OPENAI_API_KEY:
            prompt = (
                "Write 3 short posts for a brand called 'The Quiet Optimizer'. "
                "Theme: anime. Tone: calm, strategic, motivational. "
                "Each post 1–2 sentences. No hashtags."
            )
            return openai_generate(prompt)
        return pick_template("anime")

    if low.startswith("/gaming"):
        if OPENAI_API_KEY:
            prompt = (
                "Write 3 short posts for 'The Quiet Optimizer'. "
                "Theme: gaming discipline and improvement. Tone: calm, strategic. "
                "Each post 1–2 sentences. No hashtags."
            )
            return openai_generate(prompt)
        return pick_template("gaming")

    if low.startswith("/psychology"):
        if OPENAI_API_KEY:
            prompt = (
                "Write 3 short posts for 'The Quiet Optimizer'. "
                "Theme: psychology (habits, focus, resilience). Tone: calm, practical. "
                "Each post 1–2 sentences. No hashtags."
            )
            return openai_generate(prompt)
        return pick_template("psychology")

    if low.startswith("/strategy"):
        if OPENAI_API_KEY:
            prompt = (
                "Write 3 short posts for 'The Quiet Optimizer'. "
                "Theme: strategy and decision-making. Tone: calm, sharp. "
                "Each post 1–2 sentences. No hashtags."
            )
            return openai_generate(prompt)
        return pick_template("strategy")

    # Normal messages: short reply (AI if available, else template)
    if OPENAI_API_KEY:
        prompt = (
            "You are 'The Quiet Optimizer'—calm, strategic, supportive. "
            "Reply in 1–2 sentences. No emojis unless user used them.\n\n"
            f"User message: {t}"
        )
        return openai_generate(prompt)

    # Template-only “chat” fallback
    return "I’m online. Use /anime /gaming /psychology /strategy or /help."

# -----------------------------
# Web routes
# -----------------------------
@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Quiet Optimizer Online", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Telegram webhook endpoint.
    MUST always return 200 quickly, or Telegram will retry and flood you.
    """
    try:
        update = request.get_json(silent=True) or {}
        # Print minimal info for debugging (safe)
        # print("Incoming update keys:", list(update.keys()))

        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = (message.get("text") or "").strip()

        if not chat_id:
            return "OK", 200

        # Simple anti-spam throttle per chat
        now = int(time.time())
        last = LAST_MESSAGE_AT.get(chat_id, 0)
        if now - last < MIN_SECONDS_BETWEEN_MESSAGES:
            return "OK", 200
        LAST_MESSAGE_AT[chat_id] = now

        if not text:
            return "OK", 200

        reply = handle_text(text)
        send_telegram(chat_id, reply)

    except Exception as e:
        # Never crash the webhook
        print("Webhook error:", repr(e))

    return "OK", 200


# Local dev only (Render uses gunicorn)
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
```0
