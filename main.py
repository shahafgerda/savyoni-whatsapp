"""FastAPI app: receives Green API webhooks, replies via the agent.

Audience: this bot is 'public' (customer_service) - it answers anyone who
writes in a private chat, and ignores group chats. It dedupes by Green API
message id (survives Render restarts) and never answers its own messages.
"""
from fastapi import FastAPI, Request

import database
from agent import handle_message
from config import GREEN_API_INSTANCE, SPEC
from tools.whatsapp import send_reply

app = FastAPI(title="WhatsApp Agent - סביוני")

ANSWER_GROUPS = SPEC.get("audience", {}).get("answer_groups", False)


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

    # Extract text.
    message_data = body.get("messageData", {})
    text = ""
    if message_data.get("typeMessage") == "textMessage":
        text = message_data.get("textMessageData", {}).get("textMessage", "")
    elif message_data.get("typeMessage") == "extendedTextMessage":
        text = message_data.get("extendedTextMessageData", {}).get("text", "")

    if not text.strip():
        database.mark_processed(id_message)
        return {"ignored": "no text content"}

    sender_phone = chat_id.replace("@c.us", "")
    reply = handle_message(chat_id, sender_phone, text)

    try:
        send_reply(chat_id, reply)
    except Exception as exc:  # noqa: BLE001
        print(f"[main] failed to send reply: {exc}")

    database.mark_processed(id_message)
    return {"status": "handled"}
