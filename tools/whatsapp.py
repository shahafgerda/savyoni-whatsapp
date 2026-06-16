"""Outbound WhatsApp helpers (framework-only, not LLM tools).

These are used by main.py to send the bot's reply, and by future tools
(e.g. reminders) to message a user. They are NOT registered in
TOOL_REGISTRY - the LLM never calls them directly.
"""
import httpx

from config import GREEN_API_INSTANCE, GREEN_API_TOKEN, GREEN_API_URL


def _send(chat_id: str, text: str) -> dict:
    url = (
        f"{GREEN_API_URL}/waInstance{GREEN_API_INSTANCE}"
        f"/sendMessage/{GREEN_API_TOKEN}"
    )
    resp = httpx.post(url, json={"chatId": chat_id, "message": text}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def send_reply(chat_id: str, text: str) -> dict:
    """Send text to an existing chat_id (e.g. '972501234567@c.us')."""
    return _send(chat_id, text)


def send_to_phone(phone_e164: str, text: str) -> dict:
    """Send text to a phone number. phone_e164 like '972501234567'."""
    digits = phone_e164.lstrip("+").replace("-", "").replace(" ", "")
    return _send(f"{digits}@c.us", text)
