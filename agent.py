"""The agent: turns an incoming message into a reply.

handle_message() loads conversation history, builds the system prompt,
asks the LLM, runs any tools it requested, and returns the final text.

Right now the bot has no external tools, so the tool loop simply doesn't
fire. The structure is kept so wa-connect can register tools later
without rewriting this file.
"""
from google import genai
from google.genai import types

import database
from config import GOOGLE_API_KEY, LLM_MODEL
from prompt import build_system_prompt
from tools import TOOL_REGISTRY

# Parameters the framework owns - never the LLM. When a tool that acts on
# "the current user" is added (reminders, human handoff), put its name here
# so the real chat_id from the webhook is injected, not an LLM-chosen value.
FRAMEWORK_INJECTED_CHAT_ID: set[str] = set()

MAX_TOOL_ITERATIONS = 5

_client = genai.Client(api_key=GOOGLE_API_KEY)


def _history_to_contents(history) -> list[dict]:
    contents = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    return contents


def handle_message(chat_id: str, sender_phone: str, message_text: str) -> str:
    database.append(chat_id, "user", message_text)

    history = database.tail(chat_id)
    contents = _history_to_contents(history)

    system_prompt = build_system_prompt(TOOL_REGISTRY)

    config = types.GenerateContentConfig(system_instruction=system_prompt)

    try:
        response = _client.models.generate_content(
            model=LLM_MODEL,
            contents=contents,
            config=config,
        )
        reply = (response.text or "").strip()
    except Exception as exc:  # noqa: BLE001 - surface a friendly message
        print(f"[agent] LLM error: {exc}")
        reply = "מצטערים, יש תקלה זמנית. נא לפנות למזכירות בית הספר בטלפון 03-6312858."

    if not reply:
        reply = "מצטערים, לא הצלחתי להבין. נא לפנות למזכירות בית הספר בטלפון 03-6312858."

    database.append(chat_id, "assistant", reply)
    return reply
