"""FastAPI app: receives Green API webhooks, replies with a fixed message.

סביוני is a fixed auto-responder. Every private incoming message gets the
same canned reply directing the sender to the school secretariat. No LLM is
involved - the reply is deterministic, instant, and cannot hallucinate.

Group chats are ignored. The bot never answers its own messages, and dedupes
by Green API message id so a Render restart doesn't double-reply.

Verbose logging on every webhook so we can see exactly which decision the
bot takes for each incoming message.
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

    type_webhook = body.get("typeWebhook")
    if type_webhook != "incomingMessageReceived":
        print(f"[wh] skip: typeWebhook={type_webhook}")
        return {"ignored": "not an incoming message"}

    id_message = body.get("idMessage", "")
    sender_data = body.get("senderData", {})
    chat_id = sender_data.get("chatId", "")
    sender = sender_data.get("sender", "")

    is_group = chat_id.endswith("@g.us")
    print(f"[wh] in id={id_message} chat={chat_id} group={is_group}")

    # Ignore group chats unless the spec opts in.
    if is_group and not ANSWER_GROUPS:
        return {"ignored": "group chat"}

    # Never answer our own outgoing messages.
    own_jid = f"{GREEN_API_INSTANCE}@c.us"
    if sender == own_jid:
        print(f"[wh] skip: own message ({sender})")
        return {"ignored": "own message"}

    # Dedup: Render replays the last webhook on restart.
    if database.already_processed(id_message):
        print(f"[wh] skip: duplicate id={id_message}")
        return {"ignored": "duplicate"}

    # Fixed auto-reply to every incoming message, regardless of content.
    print(f"[wh] REPLYING to {chat_id}")
    try:
        result = send_reply(chat_id, AUTO_REPLY)
        print(f"[wh] send OK -> {result}")
    except Exception as exc:  # noqa: BLE001
        print(f"[wh] send FAILED: {type(exc).__name__}: {exc}")

    database.mark_processed(id_message)
    return {"status": "handled"}
