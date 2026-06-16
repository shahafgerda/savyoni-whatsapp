"""FastAPI app: receives Green API webhooks, replies with a fixed message.

סביוני is a fixed auto-responder. Every private incoming message gets the
same canned reply directing the sender to the school secretariat. No LLM is
involved - the reply is deterministic, instant, and cannot hallucinate.

Group chats are ignored. The bot never answers its own messages, and dedupes
by Green API message id so a Render restart doesn't double-reply.
"""
from fastapi import FastAPI, Request

import database
from config import GREEN_API_INSTANCE, SPEC
from tools.whatsapp import send_reply

app = FastAPI(title="WhatsApp Agent - סביוני")

ANSWER_GROUPS = SPEC.get("audience", {}).get("answer_groups", False)

# The single fixed reply this bot sends to every incoming message.
AUTO_REPLY = SPEC["fixed_auto_reply"]["message"]


@app.on_event("startup")
def _startup() -> None:
    database.init_db()


@app.get("/health")
def health():
    return {"status": "ok", "version": 1, "bot": SPEC["identity"]["name"]}


@app.post("/webhook/green-api")
async def green_api_webhook(request: Request):
    body = await request.json()

    if body.get("typeWebhook") != "incomingMessageReceived":
        return {"ignored": "not an incoming message"}

    id_message = body.get("idMessage", "")
    sender_data = body.get("senderData", {})
    chat_id = sender_data.get("chatId", "")
    sender = sender_data.get("sender", "")

    # Ignore group chats unless the spec opts in.
    if chat_id.endswith("@g.us") and not ANSWER_GROUPS:
        return {"ignored": "group chat"}

    # Never answer our own outgoing messages.
    own_jid = f"{GREEN_API_INSTANCE}@c.us"
    if sender == own_jid:
        return {"ignored": "own message"}

    # Dedup: Render replays the last webhook on restart.
    if database.already_processed(id_message):
        return {"ignored": "duplicate"}

    # Fixed auto-reply to every incoming message, regardless of content.
    try:
        send_reply(chat_id, AUTO_REPLY)
    except Exception as exc:  # noqa: BLE001
        print(f"[main] failed to send reply: {exc}")

    database.mark_processed(id_message)
    return {"status": "handled"}
